"""Native desktop interface; all analysis calls the same CLI/core functions."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime
import json
import os
import queue
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from .pipeline import Parameters,run
from .io import read_image,read_labels,export_result,label_rgb,overlay,object_table,write_json
from .metrics import evaluate,compare_labels
from .datasets import synthetic,records

ROOT=Path(__file__).resolve().parents[1]
BG='#101923'; PANEL='#192633'; INK='#edf5f7'; MUTED='#9aaebc'; ACCENT='#59dec3'


class App:
    def __init__(self,root):
        self.root=root; root.title('MorphoLab · PTIT nhóm 1')
        root.geometry('1440x930'); root.minsize(1080,720); root.configure(bg=BG)
        self.image=None; self.imagepath=None; self.truth=None; self.result=None
        self.reference=None; self.diff=None; self.last_output=None
        self.events=queue.Queue(); self.busy=False; self.actions=[]
        self.vars={}; self.metrics={}
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10),background=PANEL,foreground=INK)
        style.configure('TFrame',background=BG)
        style.configure('Panel.TFrame',background=PANEL)
        style.configure('TLabel',background=PANEL,foreground=INK)
        style.configure('Muted.TLabel',foreground=MUTED)
        style.configure('TButton',padding=(10,7),background='#2a3e50',foreground=INK,borderwidth=0)
        style.map('TButton',background=[('active','#365569'),('disabled','#24303b')],foreground=[('disabled','#778c9b')])
        style.configure('Accent.TButton',background=ACCENT,foreground='#102720',font=('Segoe UI',10,'bold'))
        style.map('Accent.TButton',background=[('active','#89edd9'),('disabled','#355a55')])
        style.configure('TNotebook',background=BG,borderwidth=0)
        style.configure('TNotebook.Tab',padding=(16,9),background=PANEL)
        style.map('TNotebook.Tab',background=[('selected','#294250')],foreground=[('selected',ACCENT)])
        style.configure('TEntry',fieldbackground='#f5f8fa',foreground='#122330',padding=4)
        style.configure('TSpinbox',fieldbackground='#f5f8fa',foreground='#122330',padding=3)
        style.configure('TCombobox',fieldbackground='#f5f8fa',foreground='#122330',padding=3)
        style.map('TCombobox',fieldbackground=[('readonly','#f5f8fa')],foreground=[('readonly','#122330')])
        style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=INK,rowheight=27)
        style.configure('Treeview.Heading',background='#294250',foreground=INK,font=('Segoe UI',9,'bold'))
        style.configure('TCheckbutton',background=PANEL,foreground=INK)
        self.build()
        root.after(100,self.poll)
        self.status.set('Sẵn sàng · Chọn ảnh hoặc mở dữ liệu mẫu để bắt đầu.')

    def button(self,parent,text,command,accent=False,**pack):
        b=ttk.Button(parent,text=text,command=command,style='Accent.TButton' if accent else 'TButton')
        b.pack(**pack); self.actions.append(b); return b

    def build(self):
        header=tk.Frame(self.root,bg=BG); header.pack(fill='x',padx=22,pady=(18,12))
        tk.Label(header,text='MORPHO',fg=INK,bg=BG,font=('Segoe UI',23,'bold')).pack(side='left')
        tk.Label(header,text='LAB',fg=ACCENT,bg=BG,font=('Segoe UI',23,'bold')).pack(side='left',padx=(5,18))
        tk.Label(header,text='PTIT / NHÓM 1\nHình thái học & Watershed',fg=MUTED,bg=BG,justify='left',font=('Segoe UI',10)).pack(side='left')
        self.button(header,'Chọn ảnh…',self.open_image,side='right',padx=4)
        self.button(header,'Ảnh tế bào thật',self.real_demo,side='right',padx=4)
        self.button(header,'Ảnh mẫu có nhãn',self.demo,side='right',padx=4)
        body=ttk.Frame(self.root); body.pack(fill='both',expand=True,padx=20)
        sideholder=ttk.Frame(body,style='Panel.TFrame',width=295)
        sideholder.pack(side='left',fill='y',padx=(0,16)); sideholder.pack_propagate(False)
        settings_canvas=tk.Canvas(sideholder,bg=PANEL,highlightthickness=0,width=280)
        settings_scroll=ttk.Scrollbar(sideholder,orient='vertical',command=settings_canvas.yview)
        settings_scroll.pack(side='right',fill='y'); settings_canvas.pack(side='left',fill='both',expand=True)
        settings_canvas.configure(yscrollcommand=settings_scroll.set)
        sidebar=ttk.Frame(settings_canvas,style='Panel.TFrame')
        settings_window=settings_canvas.create_window((0,0),window=sidebar,anchor='nw')
        sidebar.bind('<Configure>',lambda e:settings_canvas.configure(scrollregion=settings_canvas.bbox('all')))
        settings_canvas.bind('<Configure>',lambda e:settings_canvas.itemconfigure(settings_window,width=e.width))
        def wheel(event):
            widget=self.root.winfo_containing(event.x_root,event.y_root)
            if widget and str(widget).startswith(str(sideholder)):
                settings_canvas.yview_scroll(-int(event.delta/120),'units')
        self.root.bind_all('<MouseWheel>',wheel,add='+')
        tk.Label(sidebar,text='THIẾT LẬP THÍ NGHIỆM',bg=PANEL,fg=ACCENT,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=16,pady=(16,12))
        defaults=asdict(Parameters())
        def field(key,title,values=None,limits=None):
            box=ttk.Frame(sidebar,style='Panel.TFrame'); box.pack(fill='x',padx=15,pady=4)
            ttk.Label(box,text=title).pack(anchor='w',pady=(0,3))
            var=tk.StringVar(value=str(defaults[key])); self.vars[key]=var
            if values:
                widget=ttk.Combobox(box,textvariable=var,values=values,state='readonly')
            else:
                low,high,step=limits
                widget=ttk.Spinbox(box,textvariable=var,from_=low,to=high,increment=step)
            widget.pack(fill='x')
        field('engine','Bản cài đặt',('custom','library'))
        field('mode','Phương pháp',('ccl','raw','hmax','adaptive'))
        field('operation','Xử lý hình thái',('none','erosion','dilation','opening','closing','opening_closing','opening_reconstruction'))
        both=ttk.Frame(sidebar,style='Panel.TFrame'); both.pack(fill='x',padx=15,pady=5)
        ttk.Label(both,text='Phần tử cấu trúc / liên thông').pack(anchor='w')
        self.vars['shape']=tk.StringVar(value='disk'); self.vars['connectivity']=tk.StringVar(value='4')
        ttk.Combobox(both,textvariable=self.vars['shape'],values=['disk','square','cross'],state='readonly',width=12).pack(side='left',pady=4)
        ttk.Combobox(both,textvariable=self.vars['connectivity'],values=['4','8'],state='readonly',width=6).pack(side='right',pady=4)
        field('radius','Bán kính SE (pixel)',limits=(0,50,1))
        field('sigma','Gaussian sigma',limits=(0,20,.25))
        field('threshold','Ngưỡng [0–1] · -1 = Otsu',limits=(-1,1,.05))
        field('min_area','Diện tích tối thiểu (pixel²)',limits=(0,100000,5))
        field('h','Độ cao h của cực đại',limits=(.1,1000,.5))
        field('adaptive_fraction','Tỉ lệ h thích nghi',limits=(0,1,.05))
        self.vars['fill_holes']=tk.BooleanVar(value=True); self.vars['bright_foreground']=tk.BooleanVar(value=True)
        ttk.Checkbutton(sidebar,text='Lấp lỗ bằng reconstruction',variable=self.vars['fill_holes']).pack(anchor='w',padx=13,pady=4)
        ttk.Checkbutton(sidebar,text='Đối tượng sáng trên nền tối',variable=self.vars['bright_foreground']).pack(anchor='w',padx=13,pady=4)
        self.button(sidebar,'▶  Phân đoạn',self.segment,accent=True,fill='x',padx=15,pady=(12,5))
        settings=ttk.Frame(sidebar,style='Panel.TFrame'); settings.pack(fill='x',padx=15,pady=4)
        self.button(settings,'Lưu cấu hình',self.save_config,side='left',fill='x',expand=True,padx=(0,3))
        self.button(settings,'Nạp cấu hình',self.load_config,side='left',fill='x',expand=True)
        tk.Label(sidebar,text='custom = thuật toán tự cài\nlibrary = bản thư viện đối chiếu',justify='left',bg=PANEL,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=15,pady=10)
        content=ttk.Frame(body); content.pack(side='left',fill='both',expand=True)
        cards=ttk.Frame(content); cards.pack(fill='x',pady=(0,12))
        self.cards={}
        for key,title in [('objects','ĐỐI TƯỢNG'),('markers','MARKER'),('time','THỜI GIAN'),('f1','F1 ĐỐI TƯỢNG')]:
            box=tk.Frame(cards,bg=PANEL); box.pack(side='left',fill='both',expand=True,padx=(0,8))
            tk.Label(box,text=title,bg=PANEL,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=14,pady=(10,2))
            var=tk.StringVar(value='—'); self.cards[key]=var
            tk.Label(box,textvariable=var,bg=PANEL,fg=ACCENT,font=('Segoe UI',22,'bold')).pack(anchor='w',padx=14,pady=(0,10))
        self.file_label=tk.StringVar(value='Chưa có ảnh · TIFF / PNG / JPG / BMP')
        tk.Label(content,textvariable=self.file_label,bg=BG,fg=MUTED,anchor='w',font=('Segoe UI',10)).pack(fill='x',pady=(0,8))
        self.tabs=ttk.Notebook(content); self.tabs.pack(fill='both',expand=True)
        self.work=ttk.Frame(self.tabs); self.comp=ttk.Frame(self.tabs); self.batch=ttk.Frame(self.tabs); self.help=ttk.Frame(self.tabs)
        for tab,name in [(self.work,'01  Phân đoạn'),(self.comp,'02  Fiji & đánh giá'),(self.batch,'03  Benchmark'),(self.help,'04  Thuật toán & cách dùng')]: self.tabs.add(tab,text=name)
        bar=ttk.Frame(self.work); bar.pack(fill='x',pady=8)
        self.view=tk.StringVar(value='Tổng quan 6 bước')
        chooser=ttk.Combobox(bar,textvariable=self.view,state='readonly',width=23,
            values=['Tổng quan 6 bước','gray','smoothed','binary','erosion','dilation','morphology','mask','components','distance','elevation','markers','labels'])
        chooser.pack(side='left'); chooser.bind('<<ComboboxSelected>>',lambda _:self.draw())
        self.button(bar,'Xuất toàn bộ kết quả',self.export,side='right',padx=3)
        self.button(bar,'Mở thư mục kết quả',self.open_output,side='right',padx=3)
        self.fig=Figure(figsize=(10,5.4),facecolor=BG,layout='constrained')
        self.canvas=FigureCanvasTkAgg(self.fig,master=self.work); self.canvas.get_tk_widget().pack(fill='both',expand=True)
        self.canvas.mpl_connect('button_press_event',self.inspect_object)
        nav=ttk.Frame(self.work); nav.pack(fill='x'); NavigationToolbar2Tk(self.canvas,nav,pack_toolbar=False).pack(side='left')
        self.object_info=tk.StringVar(value='Chọn một vật thể trên ảnh kết quả để xem diện tích và tâm.')
        tk.Label(self.work,textvariable=self.object_info,bg=BG,fg=MUTED,anchor='w',wraplength=1000).pack(fill='x',pady=5)
        refbar=ttk.Frame(self.comp); refbar.pack(fill='x',pady=8)
        self.button(refbar,'Nạp ground truth…',self.open_truth,side='left',padx=3)
        self.button(refbar,'Chạy Fiji / MorphoLibJ',self.fiji,accent=True,side='left',padx=3)
        self.button(refbar,'Workflow Fiji độc lập',lambda:self.fiji(native=True),side='left',padx=3)
        self.button(refbar,'Nạp kết quả Fiji…',self.import_reference,side='left',padx=3)
        self.button(refbar,'Thư mục Fiji…',self.choose_fiji,side='right',padx=3)
        self.fiji_home=r'C:\Tools\Fiji'
        self.cfig=Figure(figsize=(10,3),facecolor=BG,layout='constrained')
        self.ccanvas=FigureCanvasTkAgg(self.cfig,master=self.comp); self.ccanvas.get_tk_widget().pack(fill='both',expand=True)
        self.metric_tree=ttk.Treeview(self.comp,columns=('metric','python','fiji'),show='headings',height=8)
        for col,text,width in [('metric','Chỉ số',300),('python','Python → ground truth',220),('fiji','Fiji → ground truth',220)]:
            self.metric_tree.heading(col,text=text); self.metric_tree.column(col,width=width,anchor='w')
        self.metric_tree.pack(fill='x',pady=6)
        self.comparison_note=tk.StringVar(value='Ground truth đánh giá độ đúng; Fiji kiểm chứng triển khai. IoU ghép đối tượng ≥ 0.5.')
        tk.Label(self.comp,textvariable=self.comparison_note,bg=BG,fg=MUTED,wraplength=1000,justify='left').pack(fill='x',pady=6)
        self.build_batch()
        self.build_help()
        self.status=tk.StringVar()
        tk.Label(self.root,textvariable=self.status,bg=BG,fg=MUTED,anchor='w',font=('Segoe UI',10)).pack(fill='x',padx=22,pady=10)
        self.draw(); self.draw_compare()

    def build_batch(self):
        options=ttk.Frame(self.batch); options.pack(fill='x',pady=10)
        self.dataset=tk.StringVar(value='synthetic')
        self.split=tk.StringVar(value='validation'); self.limit=tk.StringVar(value='6'); self.repeats=tk.StringVar(value='3')
        for title,var,values,width in [('Dataset',self.dataset,['synthetic','bbbc039'],14),('Split',self.split,['validation','test','training'],12)]:
            ttk.Label(options,text=title).pack(side='left',padx=5)
            ttk.Combobox(options,textvariable=var,values=values,state='readonly',width=width).pack(side='left')
        for title,var in [('Số ảnh',self.limit),('Lặp đo',self.repeats)]:
            ttk.Label(options,text=title).pack(side='left',padx=5)
            ttk.Spinbox(options,textvariable=var,from_=1,to=200,width=4).pack(side='left')
        actions=ttk.Frame(self.batch); actions.pack(fill='x',pady=4)
        self.button(actions,'Chạy 4 phương pháp × 2 bản',self.benchmark,accent=True,side='left',padx=3)
        self.button(actions,'Khảo sát h trên validation',self.sweep,side='left',padx=3)
        self.button(actions,'Chuẩn bị BBBC039',self.prepare_real,side='left',padx=3)
        self.button(actions,'Xử lý thư mục ảnh…',self.batch_folder,side='left',padx=3)
        tk.Label(self.batch,text='Benchmark loại thời gian đọc/ghi ảnh và tính metric; có 1 lượt warm-up. Chỉ chọn tham số trên validation.',
            bg=BG,fg=MUTED,wraplength=980,justify='left').pack(fill='x',pady=8)
        self.bfig=Figure(figsize=(10,3.8),facecolor=BG,layout='constrained')
        self.bcanvas=FigureCanvasTkAgg(self.bfig,master=self.batch); self.bcanvas.get_tk_widget().pack(fill='both',expand=True)
        self.log=tk.Text(self.batch,height=8,bg=PANEL,fg=INK,insertbackground=INK,font=('Consolas',9),relief='flat',wrap='word')
        self.log.pack(fill='x',pady=6)

    def build_help(self):
        text=tk.Text(self.help,bg=BG,fg=INK,font=('Segoe UI',11),wrap='word',padx=24,pady=20,relief='flat')
        scroll=ttk.Scrollbar(self.help,command=text.yview); text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y'); text.pack(fill='both',expand=True)
        text.tag_configure('title',font=('Segoe UI',18,'bold'),foreground=ACCENT)
        text.insert('end','Từ ảnh đến từng đối tượng\n\n','title')
        text.insert('end',HELP)
        text.configure(state='disabled')

    def parameters(self):
        floats={'sigma','threshold','h','adaptive_fraction'}; ints={'radius','min_area','connectivity'}
        values={k:(float(v.get()) if k in floats else int(v.get()) if k in ints else v.get()) for k,v in self.vars.items()}
        return Parameters(**values).validate()

    def job(self,function,done,message):
        if self.busy: return
        self.busy=True; self.status.set(message)
        for b in self.actions: b.configure(state='disabled')
        def worker():
            try: self.events.put(('done',(done,function())))
            except Exception as exc: self.events.put(('error',(str(exc),traceback.format_exc())))
        threading.Thread(target=worker,daemon=True).start()

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='log':
                    self.log.insert('end',value+'\n'); self.log.see('end'); self.status.set(value)
                else:
                    self.busy=False
                    for b in self.actions: b.configure(state='normal')
                    if kind=='done':
                        callback,result=value
                        try: callback(result)
                        except Exception as exc: self.error(str(exc))
                    else:
                        self.log.insert('end',value[1]+'\n'); self.error(value[0])
        except queue.Empty: pass
        self.root.after(100,self.poll)

    def error(self,message):
        self.status.set('Chưa hoàn tất · '+message[:150]); messagebox.showerror('MorphoLab',message,parent=self.root)

    def set_image(self,path,truthpath=None):
        try:
            image=read_image(path)
            truth=read_labels(truthpath,image.shape) if truthpath else None
        except Exception as exc: self.error(str(exc)); return
        self.image=image; self.imagepath=Path(path); self.truth=truth
        self.result=None; self.reference=None; self.diff=None
        self.file_label.set(f'{self.imagepath.name}  ·  {image.shape[1]} × {image.shape[0]}  ·  '+('Có ground truth' if truth is not None else 'Chưa có ground truth'))
        for var in self.cards.values(): var.set('—')
        self.draw(); self.draw_compare(); self.refresh_metrics()
        self.tabs.select(self.work); self.status.set('Ảnh đã nạp · Nhấn Phân đoạn để chạy với tham số bên trái.')

    def open_image(self):
        name=filedialog.askopenfilename(parent=self.root,title='Chọn ảnh 2D',filetypes=[('Images','*.tif *.tiff *.png *.jpg *.jpeg *.bmp'),('All','*.*')])
        if name: self.set_image(name)

    def demo(self):
        if not (ROOT/'data/synthetic/manifest.json').exists(): synthetic(ROOT/'data')
        self.set_image(ROOT/'data/synthetic/synth_00.tif',ROOT/'data/synthetic/synth_00_gt.tif')

    def real_demo(self):
        manifest=ROOT/'data/bbbc039/manifest.json'
        if not manifest.exists():
            self.error('Chọn tab Benchmark → Chuẩn bị BBBC039 trước.'); return
        _,image,truth=records(manifest,'validation',1)[0]; self.set_image(image,truth)

    def segment(self):
        if self.image is None: self.error('Hãy chọn ảnh trước.'); return
        try: params=self.parameters()
        except Exception as exc: self.error(str(exc)); return
        image=self.image.copy()
        self.job(lambda:run(image,params),self.segment_done,'Đang phân đoạn · giao diện vẫn có thể xem các tab…')

    def segment_done(self,result):
        self.result=result; self.reference=None; self.diff=None
        self.cards['objects'].set(str(np.unique(result.labels[result.labels>0]).size))
        self.cards['markers'].set(str(np.unique(result.stages['markers'][result.stages['markers']>0]).size))
        self.cards['time'].set(f'{result.timings["total"]:.3f} s')
        self.draw(); self.draw_compare(); self.refresh_metrics()
        self.status.set(f'Hoàn tất · {result.params.engine}/{result.params.mode} · Ngưỡng={result.threshold:.4f} · Có thể xuất kết quả hoặc kiểm chứng Fiji.')

    def draw(self):
        self.fig.clear()
        if self.image is None:
            ax=self.fig.add_subplot(); ax.set_facecolor(BG); ax.axis('off')
            ax.text(.5,.62,'Phân đoạn từng đối tượng',ha='center',color=INK,fontsize=23,transform=ax.transAxes)
            ax.text(.5,.46,'Mở ảnh mẫu có nhãn → Phân đoạn → Kiểm chứng Fiji',ha='center',color=MUTED,fontsize=12,transform=ax.transAxes)
        elif self.result is None:
            ax=self.fig.add_subplot(); self.show(ax,self.image,'Ảnh đầu vào','gray')
        else:
            titles={'gray':'01 · Ảnh gốc','binary':'02 · Ngưỡng','mask':'03 · Mask sau hình thái',
                'distance':'04 · Khoảng cách tới nền','markers':'05 · Marker','labels':'06 · Đối tượng đã tách'}
            keys=['gray','binary','mask','distance','markers','labels'] if self.view.get()=='Tổng quan 6 bước' else [self.view.get()]
            for i,key in enumerate(keys):
                ax=self.fig.add_subplot(2,3,i+1) if len(keys)>1 else self.fig.add_subplot()
                array=self.result.stages[key]
                if key=='labels': array=overlay(self.image,array)
                elif key in ('markers','components'): array=label_rgb(array)
                self.show(ax,array,titles.get(key,key),'magma' if key in ('distance','elevation') else 'gray')
        self.canvas.draw_idle()

    @staticmethod
    def show(ax,array,title,cmap='gray'):
        ax.set_facecolor(BG); ax.imshow(array,cmap=cmap,interpolation='nearest')
        ax.set_title(title,color=INK,fontsize=10,loc='left',pad=8); ax.axis('off')

    def draw_compare(self):
        self.cfig.clear()
        for i,title in enumerate(['Python','Fiji / MorphoLibJ','Vùng khác sau ghép ID nhãn']):
            ax=self.cfig.add_subplot(1,3,i+1); ax.set_facecolor(BG); ax.axis('off')
            array=None
            if i==0 and self.result is not None: array=overlay(self.image,self.result.labels)
            if i==1 and self.reference is not None: array=overlay(self.image,self.reference)
            if i==2 and self.diff is not None: array=self.diff
            if array is not None: self.show(ax,array,title,'inferno')
            else: ax.text(.5,.5,title+'\nChưa có kết quả',ha='center',color=MUTED,transform=ax.transAxes)
        self.ccanvas.draw_idle()

    def inspect_object(self,event):
        if self.result is None or event.xdata is None or event.ydata is None: return
        y,x=int(event.ydata+.5),int(event.xdata+.5)
        if not (0<=y<self.result.labels.shape[0] and 0<=x<self.result.labels.shape[1]): return
        idx=int(self.result.labels[y,x])
        if not idx: self.object_info.set('Vị trí đang chọn thuộc nền.'); return
        row=object_table(self.result.labels,self.image).set_index('label').loc[idx]
        self.object_info.set(f'Đối tượng #{idx} · Diện tích {row["area"]:.0f} pixel² · Tâm (x={row["centroid-1"]:.1f}, y={row["centroid-0"]:.1f}) · Đường kính tương đương {row["equivalent_diameter_area"]:.1f} pixel')

    def open_truth(self):
        if self.image is None: self.error('Hãy chọn ảnh trước'); return
        name=filedialog.askopenfilename(parent=self.root,title='Nhãn 2D số nguyên; nền 0; mỗi vật thể một ID',filetypes=[('Labels','*.tif *.tiff *.png')])
        if not name: return
        try: self.truth=read_labels(name,self.image.shape); self.refresh_metrics()
        except Exception as exc: self.error(str(exc))

    def refresh_metrics(self):
        self.metric_tree.delete(*self.metric_tree.get_children())
        self.cards['f1'].set('—')
        if self.result is None or self.truth is None: return
        metrics=evaluate(self.truth,self.result.labels)
        self.cards['f1'].set(f'{metrics["object_f1"]:.3f}')
        reference=evaluate(self.truth,self.reference) if self.reference is not None else {}
        names={'foreground_iou':'IoU tiền cảnh','foreground_dice':'Dice tiền cảnh','object_f1':'F1 đối tượng (IoU ≥ 0.5)',
            'panoptic_quality':'Panoptic quality','count_absolute_error':'Sai số đếm','split_objects':'Đối tượng bị chia','merge_objects':'Đối tượng bị gộp','true_objects':'Số đối tượng đúng'}
        for key,title in names.items():
            fmt=lambda val:f'{val:.4f}' if isinstance(val,float) else str(val)
            self.metric_tree.insert('',tk.END,values=(title,fmt(metrics[key]),fmt(reference[key]) if key in reference else '—'))

    def output_folder(self,prefix):
        return ROOT/'outputs'/f'{prefix}_{datetime.now():%Y%m%d_%H%M%S_%f}'

    def fiji(self,native=False):
        if self.result is None: self.error('Hãy chạy phân đoạn trước'); return
        if self.result.params.mode=='ccl': self.error('CCL chưa phải Watershed. Hãy chọn raw/hmax/adaptive rồi phân đoạn lại để kiểm chứng Watershed.'); return
        from .fiji import run_reference
        folder=self.output_folder('fiji'); result=self.result; truth=self.truth; home=self.fiji_home
        def done(value):
            labels,stats,self.diff=value; self.reference=labels; self.last_output=folder
            self.draw_compare(); self.refresh_metrics(); self.tabs.select(self.comp)
            score=stats['comparison']['matched_pixel_agreement_foreground_union']
            protocol='Workflow Fiji độc lập (SE vuông, Otsu 8-bit, ImageJ EDM)' if native else 'Cùng địa hình/marker/mask; có thể khác ở plateau'
            self.comparison_note.set(f'Đồng thuận pixel sau ghép ID: {score:.2%}. {protocol}. fiji_metrics.csv do Java/ImageJ tính.')
            self.status.set('Đã chạy MorphoLibJ thật · '+str(folder))
        self.job(lambda:run_reference(result,folder,truth,home,native=native),done,'Đang gọi Fiji / MorphoLibJ bằng Java…')

    def choose_fiji(self):
        path=filedialog.askdirectory(parent=self.root,title='Chọn thư mục Fiji chứa jars, plugins, java')
        if path: self.fiji_home=path; self.status.set('Fiji: '+path)

    def import_reference(self):
        if self.result is None: self.error('Hãy chạy phân đoạn trước'); return
        name=filedialog.askopenfilename(parent=self.root,title='Ảnh nhãn xuất từ Fiji',filetypes=[('Labels','*.tif *.tiff *.png')])
        if not name: return
        try:
            self.reference=read_labels(name,self.result.labels.shape)
            stats,self.diff=compare_labels(self.reference,self.result.labels)
            self.draw_compare(); self.refresh_metrics()
            self.comparison_note.set('Đồng thuận pixel sau ghép ID: '+f'{stats["matched_pixel_agreement_foreground_union"]:.2%}')
        except Exception as exc: self.error(str(exc))

    def export(self):
        if self.result is None: self.error('Hãy chạy phân đoạn trước'); return
        name=filedialog.askdirectory(parent=self.root,title='Chọn thư mục cha lưu kết quả')
        if not name: return
        folder=Path(name)/self.output_folder('run').name
        result=self.result; truth=self.truth; reference=self.reference; source=self.imagepath
        def work():
            export_result(result,folder,source)
            if truth is not None: write_json(folder/'metrics.json',evaluate(truth,result.labels))
            if reference is not None:
                import tifffile
                tifffile.imwrite(folder/'fiji_labels.tif',reference.astype(np.uint32))
                stats,diff=compare_labels(reference,result.labels); write_json(folder/'fiji_comparison.json',stats)
            return folder
        def done(path): self.last_output=path; self.status.set('Đã xuất ảnh, tham số, objects.csv và metric: '+str(path))
        self.job(work,done,'Đang xuất kết quả…')

    def open_output(self):
        path=self.last_output or ROOT/'outputs'; path.mkdir(parents=True,exist_ok=True)
        os.startfile(str(path))

    def save_config(self):
        try: params=self.parameters()
        except Exception as exc: self.error(str(exc)); return
        name=filedialog.asksaveasfilename(parent=self.root,defaultextension='.json',initialdir=str(ROOT/'configs'),filetypes=[('JSON','*.json')])
        if name: write_json(name,asdict(params)); self.status.set('Đã lưu tham số: '+name)

    def load_config(self):
        name=filedialog.askopenfilename(parent=self.root,initialdir=str(ROOT/'configs'),filetypes=[('JSON','*.json')])
        if not name: return
        try:
            params=Parameters(**json.loads(Path(name).read_text(encoding='utf-8'))).validate()
            for key,value in asdict(params).items(): self.vars[key].set(value)
            self.status.set('Đã nạp tham số · Nhấn Phân đoạn để tính lại.')
        except Exception as exc: self.error(str(exc))

    def prepare_real(self):
        from .datasets import prepare_bbbc
        self.job(lambda:prepare_bbbc(ROOT/'data',lambda s:self.events.put(('log',s))),
            lambda p:self.status.set('Dataset sẵn sàng: '+str(p)),'Đang chuẩn bị BBBC039…')

    def experiment_inputs(self):
        manifest=ROOT/'data'/self.dataset.get()/'manifest.json'
        if not manifest.exists(): raise ValueError('Hãy chuẩn bị dataset trước')
        limit=int(self.limit.get()); repeats=int(self.repeats.get())
        if not 1<=limit<=200 or not 1<=repeats<=20: raise ValueError('Số ảnh [1,200], lặp đo [1,20]')
        return manifest,limit,repeats,self.parameters()

    def benchmark(self):
        try: manifest,limit,repeats,params=self.experiment_inputs()
        except Exception as exc: self.error(str(exc)); return
        from .benchmark import benchmark
        split=self.split.get(); folder=self.output_folder('benchmark')
        self.job(lambda:benchmark(manifest,folder,params,split,limit,repeats,progress=lambda s:self.events.put(('log',s))),
            lambda value:self.benchmark_done(value,folder),'Đang benchmark; có thể mất vài phút…')

    def benchmark_done(self,value,folder):
        frame,summary=value; self.last_output=folder
        self.bfig.clear(); a,b=self.bfig.subplots(1,2)
        for ax in (a,b):
            ax.set_facecolor(PANEL); ax.tick_params(colors=INK); ax.grid(alpha=.15)
            ax.spines[['top','right']].set_visible(False)
        for engine in summary.engine.unique():
            part=summary[summary.engine==engine]
            a.plot(part['mode'],part.object_f1,'o-',label=engine)
            b.plot(part['mode'],part.seconds_median,'o-',label=engine)
        a.set_ylim(0,1.05); a.set_title('F1 đối tượng',color=INK); b.set_title('Thời gian (giây)',color=INK)
        a.legend(); b.legend(); self.bcanvas.draw_idle()
        self.log.insert('end',summary.to_string(index=False)+'\n')
        self.status.set('Benchmark hoàn tất · '+str(folder))

    def sweep(self):
        try: manifest,limit,repeats,params=self.experiment_inputs()
        except Exception as exc: self.error(str(exc)); return
        from .benchmark import sweep
        folder=self.output_folder('sweep')
        def done(table):
            self.last_output=folder; self.log.insert('end',table.to_string(index=False)+'\n')
            self.status.set('Đã khảo sát trên validation · Nạp selected_parameters.json để sử dụng; chưa đánh giá test.')
        self.job(lambda:sweep(manifest,folder,params,limit=limit,progress=lambda s:self.events.put(('log',s))),done,'Đang khảo sát h trên validation…')

    def batch_folder(self):
        try: params=self.parameters()
        except Exception as exc: self.error(str(exc)); return
        name=filedialog.askdirectory(parent=self.root,title='Chọn thư mục ảnh; nhãn đúng tùy chọn: tênảnh_gt.tif')
        if not name: return
        from .benchmark import process_folder
        folder=self.output_folder('batch')
        def done(frame):
            self.last_output=folder; self.log.insert('end',frame.to_string(index=False)+'\n')
            errors=int((frame.status=='error').sum())
            self.status.set(f'Xong {len(frame)} ảnh · {errors} lỗi · '+str(folder))
        self.job(lambda:process_folder(name,folder,params,progress=lambda s:self.events.put(('log',s))),done,'Đang xử lý thư mục ảnh…')


HELP='''CÁCH CHẠY THÍ NGHIỆM
1. Chọn ảnh mẫu có nhãn hoặc ảnh tế bào BBBC039.
2. Chọn custom (tự cài) hoặc library (thư viện đối chiếu), rồi Phân đoạn.
3. Xem từng ảnh trung gian, phóng to bằng thanh công cụ và chọn vật thể.
4. Tab Fiji & đánh giá: nạp nhãn đúng hoặc chạy MorphoLibJ thật trên máy.
5. Xuất toàn bộ ảnh TIFF, overlay, bảng đối tượng, tham số, metric và môi trường.
6. Benchmark: chọn dataset, split, số ảnh, số lần đo. Chọn tham số trên validation trước khi đánh giá test.

THUẬT TOÁN
Erosion A⊖B giữ các vị trí phần tử cấu trúc đặt lọt trong A.
Dilation A⊕B mở rộng A theo B. Opening = erosion → dilation; closing = dilation → erosion.
Reconstruction: X₀ = marker; Xₖ₊₁ = min(dilation(Xₖ), mask), lặp đến ổn định. custom dùng hàng đợi lan truyền.
Distance transform: khoảng cách Euclid tới nền. custom dùng bao dưới của các parabol, tách theo hai trục.
Watershed: địa hình âm distance map; nước lan từ marker qua hàng đợi ưu tiên. custom xử lý đồng mức theo thứ tự đến (FIFO), không tạo đường phân cách có giá trị 0.
Connected components: BFS theo liên thông 4 hoặc 8; baseline để quan sát lỗi gộp vật thể chạm nhau.

BỐN PHƯƠNG PHÁP
ccl: chỉ gán nhãn vùng liên thông, chưa tách vật thể chạm nhau.
raw: Watershed từ cực đại vùng chưa lọc theo h.
hmax: lọc cực đại bằng reconstruction với độ cao h.
adaptive: h theo từng thành phần = max(h, tỉ lệ × khoảng cách cực đại). Đây là giả thuyết thực nghiệm; cần đo mới kết luận tốt hơn.
Thành phần chưa có marker sẽ được thêm một marker tại khoảng cách lớn nhất.

QUY ƯỚC CÀI ĐẶT
Ảnh 2D; giá trị ảnh chuẩn hóa min–max [0,1]. Ngưỡng -1 dùng Otsu.
Phép hình thái dùng SE có tâm và kích thước lẻ; ngoài ảnh là nền 0.
EDT thêm một khung nền 1 pixel. Liên thông chọn 4/8 dùng xuyên suốt pipeline.
Watershed nhận elevation float32; cùng TIFF đó được đưa vào Fiji.
Pipeline dùng thư viện cho đọc/ghi, Gaussian, Otsu và thống kê; thuật toán tự cài nằm trong algorithms.py.
Tham số thay đổi chỉ có hiệu lực khi nhấn Phân đoạn. Kết quả xuất lưu đúng cấu hình đã chạy.

ĐÁNH GIÁ
Ground truth là ảnh nhãn số nguyên: nền 0, mỗi vật thể một ID. Không dùng ảnh tô màu RGB làm nhãn số.
F1: ghép một–một tối đa số cặp có IoU ≥ 0.5, rồi tối đa tổng IoU. TP = cặp khớp; FP = dự đoán thừa; FN = bỏ sót.
IoU/Dice tiền cảnh đo mask; chúng không phát hiện đầy đủ lỗi gộp vật thể.
Split/merge: liên hệ giữa hai vùng có giao ít nhất 10% diện tích vùng nhỏ hơn; đây là quy ước chẩn đoán đã công bố trong output.
Fiji là tham chiếu triển khai, không tự trở thành ground truth. Màu và ID nhãn có thể khác; so sánh sau ghép ID.
File fiji_metrics.csv do Java/ImageJ tính độc lập IoU/Dice tiền cảnh và số đối tượng.
Thời gian Python tách khỏi đọc/ghi và metric; thời gian JVM khởi động ghi riêng với thời gian Watershed Fiji.

DỮ LIỆU VÀ NGUỒN
BBBC039v1: ảnh nhân tế bào U2OS, nhãn thủ công, giấy phép CC0. Giữ nguyên training/validation/test chính thức.
https://bbbc.broadinstitute.org/BBBC039
Ảnh tổng hợp dùng seed cố định và nhãn hình học; không thay thế đánh giá trên ảnh thật.
MorphoLibJ: Legland, Arganda-Carreras, Andrey (2016), doi:10.1093/bioinformatics/btw413.
https://imagej.net/plugins/morpholibj
https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_watershed.html

PHẠM VI
Ứng dụng nghiên cứu 2D, không phải công cụ chẩn đoán. Không có mô hình học sâu.
Báo cáo ~30 trang và slides ~10 trang là sản phẩm viết riêng, sử dụng số liệu thực từ phần mềm.
'''


def launch():
    os.chdir(ROOT)
    if not (ROOT/'data/synthetic/manifest.json').exists(): synthetic(ROOT/'data')
    root=tk.Tk(); App(root); root.mainloop()
