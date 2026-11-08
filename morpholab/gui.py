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
from .ui import ChoiceVar,Tooltip,caption,OBJECT_COLUMNS,result_notice

ROOT=Path(__file__).resolve().parents[1]
BG='#0d1625'; PANEL='#17263a'; INK='#eef4fb'; MUTED='#a4b6ca'; ACCENT='#6be0cb'
BORDER='#2c4059'; FIELD='#102033'; VIOLET='#b3a6ff'


class App:
    def __init__(self,root):
        self.root=root; root.title('MorphoLab · PTIT nhóm 1')
        width=min(1440,max(1000,root.winfo_screenwidth()-60))
        height=min(930,max(640,root.winfo_screenheight()-80))
        root.geometry(f'{width}x{height}'); root.minsize(1000,640); root.configure(bg=BG)
        self.image=None; self.imagepath=None; self.truth=None; self.result=None
        self.reference=None; self.diff=None; self.last_output=None
        self.events=queue.Queue(); self.busy=False; self.actions=[]
        self.worker=None; self.token=None; self.closing=False
        self.marker_edit=tk.BooleanVar(value=False); self.manual_markers=None
        self.marker_dirty=False; self.input_widgets=[]
        self.vars={}; self.metrics={}
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10),background=PANEL,foreground=INK)
        style.configure('TFrame',background=BG)
        style.configure('Panel.TFrame',background=PANEL)
        style.configure('TLabel',background=PANEL,foreground=INK)
        style.configure('Muted.TLabel',foreground=MUTED)
        style.configure('TButton',padding=(12,8),background='#233a53',foreground=INK,borderwidth=0,focuscolor=ACCENT)
        style.map('TButton',background=[('active','#345372'),('disabled','#1c2a3e')],foreground=[('disabled','#778c9b')])
        style.configure('Accent.TButton',background=ACCENT,foreground='#102720',font=('Segoe UI',10,'bold'))
        style.map('Accent.TButton',background=[('active','#89edd9'),('disabled','#355a55')])
        style.configure('TNotebook',background=BG,borderwidth=0,tabmargins=(0,4,0,0),bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
        style.configure('TNotebook.Tab',padding=(12,10),background=PANEL,borderwidth=0,foreground=MUTED,bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
        style.map('TNotebook.Tab',background=[('selected','#28405b'),('active','#20364e')],foreground=[('selected',ACCENT)])
        style.layout('TNotebook',[('Notebook.client',{'sticky':'nswe'})])
        for name in ('TEntry','TSpinbox','TCombobox'):
            style.configure(name,fieldbackground=FIELD,background=PANEL,foreground=INK,padding=6,
                bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER,arrowcolor=MUTED,insertcolor=INK)
        style.map('TCombobox',fieldbackground=[('readonly',FIELD)],foreground=[('readonly',INK)])
        root.option_add('*TCombobox*Listbox.background',FIELD)
        root.option_add('*TCombobox*Listbox.foreground',INK)
        root.option_add('*TCombobox*Listbox.selectBackground','#2b536d')
        style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=INK,rowheight=31,borderwidth=0,bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER)
        style.configure('Treeview.Heading',background='#243d57',foreground=INK,font=('Segoe UI',9,'bold'),padding=8,bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER,relief='flat')
        style.map('Treeview',background=[('selected','#2a5669')],foreground=[('selected','#ffffff')])
        style.configure('Vertical.TScrollbar',background=BORDER,troughcolor=BG,bordercolor=BG,arrowcolor=MUTED)
        style.configure('Horizontal.TScrollbar',background=BORDER,troughcolor=BG,bordercolor=BG,arrowcolor=MUTED)
        style.configure('TCheckbutton',background=PANEL,foreground=INK)
        style.map('TCheckbutton',background=[('active',PANEL)],indicatorcolor=[('selected',ACCENT)])
        style.configure('TProgressbar',background=ACCENT,troughcolor=PANEL,borderwidth=0)
        self.build()
        root.after(100,self.poll)
        self.status.set('Sẵn sàng · Chọn ảnh hoặc mở dữ liệu mẫu để bắt đầu.')
        for var in self.vars.values(): var.trace_add('write',self.parameters_changed)
        self.marker_edit.trace_add('write',self.marker_mode_changed)
        root.protocol('WM_DELETE_WINDOW',self.close)

    def button(self,parent,text,command,accent=False,**pack):
        b=ttk.Button(parent,text=text,command=command,style='Accent.TButton' if accent else 'TButton')
        b.pack(**pack); self.actions.append(b); return b

    def build(self):
        header=tk.Frame(self.root,bg=BG); header.pack(fill='x',padx=22,pady=(18,12))
        tk.Label(header,text='MORPHO',fg=INK,bg=BG,font=('Segoe UI',23,'bold')).pack(side='left')
        tk.Label(header,text='LAB',fg=ACCENT,bg=BG,font=('Segoe UI',23,'bold')).pack(side='left',padx=(5,18))
        tk.Label(header,text='PTIT · NHÓM 1\nWatershed (phân vùng ảnh)',fg=MUTED,bg=BG,justify='left',font=('Segoe UI',10)).pack(side='left')
        self.button(header,'Chọn ảnh…',self.open_image,side='right',padx=4)
        self.button(header,'Bộ ảnh & nhãn',self.browse_dataset,side='right',padx=4)
        self.button(header,'Ảnh mẫu có nhãn',self.demo,side='right',padx=4)
        self.stop_button=ttk.Button(header,text='■ Dừng tác vụ',command=self.cancel,state='disabled')
        self.stop_button.pack(side='right',padx=8)
        steps=tk.Frame(self.root,bg=PANEL); steps.pack(fill='x',padx=20,pady=(0,12))
        tk.Label(steps,text='01  CHỌN ẢNH     →     02  CHỌN PHƯƠNG PHÁP     →     03  PHÂN ĐOẠN     →     04  KIỂM CHỨNG FIJI',
            bg=PANEL,fg=MUTED,font=('Segoe UI',9,'bold'),padx=16,pady=10).pack(anchor='w')
        body=ttk.Frame(self.root); body.pack(fill='both',expand=True,padx=20)
        sideholder=ttk.Frame(body,style='Panel.TFrame',width=355)
        sideholder.pack(side='left',fill='y',padx=(0,16)); sideholder.pack_propagate(False)
        sidebar_footer=ttk.Frame(sideholder,style='Panel.TFrame'); sidebar_footer.pack(side='bottom',fill='x')
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
        def section(title):
            tk.Label(sidebar,text=title,bg=PANEL,fg=ACCENT,font=('Segoe UI',9,'bold')).pack(anchor='w',padx=16,pady=(18,7))
        section('01 / PHƯƠNG PHÁP')
        defaults=asdict(Parameters())
        def field(key,title,values=None,limits=None):
            box=ttk.Frame(sidebar,style='Panel.TFrame'); box.pack(fill='x',padx=15,pady=4)
            ttk.Label(box,text=title).pack(anchor='w',pady=(0,3))
            var=ChoiceVar(self.root,group=key,value=defaults[key]) if values else tk.StringVar(value=str(defaults[key]))
            self.vars[key]=var
            if values:
                widget=ttk.Combobox(box,textvariable=var,values=var.display_values,state='readonly')
            else:
                low,high,step=limits
                widget=ttk.Spinbox(box,textvariable=var,from_=low,to=high,increment=step)
            widget.pack(fill='x')
            self.input_widgets.append((widget,'readonly' if values else 'normal'))
            hints={'engine':'custom: các thuật toán hình thái, tái tạo, khoảng cách, gán nhãn và Watershed tự cài. library: bản dùng thư viện để đối chiếu.',
                'mode':'CCL chỉ đếm vùng liền nhau; các cách Watershed dùng điểm khởi tạo để tách những vật thể đang chạm nhau.',
                'min_area':'Loại các vùng liên thông nhỏ hơn giá trị này trước Watershed. Nếu đặt lớn hơn toàn ảnh thì kết quả sẽ rỗng.',
                'h':'Dùng với hmax / adaptive. h càng lớn càng loại nhiều cực đại yếu, thường giảm số điểm khởi tạo. Quá lớn có thể gộp các vật thể.',
                'adaptive_fraction':'Chỉ dùng với adaptive: h riêng cho từng vùng = max(h, tỉ lệ × khoảng cách lớn nhất).',
                'threshold':'-1 dùng ngưỡng Otsu tự động. Giá trị 0–1 là ngưỡng trên ảnh đã chuẩn hóa độ sáng.',
                'radius':'Kích thước phần tử cấu trúc là 2 × bán kính + 1. Bán kính lớn có thể làm mất vật thể nhỏ.'}
            if key in hints: Tooltip(widget,hints[key])
        field('engine','Bản cài đặt',('custom','library'))
        field('mode','Phương pháp',('ccl','raw','hmax','adaptive'))
        field('operation','Xử lý hình thái',('none','erosion','dilation','opening','closing','opening_closing','opening_reconstruction'))
        section('02 / LÀM SẠCH VÙNG ẢNH')
        both=ttk.Frame(sidebar,style='Panel.TFrame'); both.pack(fill='x',padx=15,pady=5)
        ttk.Label(both,text='Phần tử cấu trúc / liên thông').pack(anchor='w')
        self.vars['shape']=ChoiceVar(self.root,group='shape',value='disk')
        self.vars['connectivity']=ChoiceVar(self.root,group='connectivity',value='4')
        for key,width in [('shape',18),('connectivity',17)]:
            widget=ttk.Combobox(both,textvariable=self.vars[key],values=self.vars[key].display_values,state='readonly',width=width)
            widget.pack(side='left',fill='x',expand=True,pady=4,padx=(0,4)); self.input_widgets.append((widget,'readonly'))
        field('radius','Bán kính SE (phần tử cấu trúc, pixel)',limits=(0,50,1))
        field('sigma','Gaussian sigma (mức làm trơn)',limits=(0,20,.25))
        field('threshold','Ngưỡng: -1 = Otsu (tự chọn), hoặc 0–1',limits=(-1,1,.05))
        field('min_area','Diện tích tối thiểu (pixel²)',limits=(0,100000,5))
        section('03 / TÁCH TỪNG ĐỐI TƯỢNG')
        field('h','Độ cao h của cực đại',limits=(.1,1000,.5))
        field('adaptive_fraction','Tỉ lệ h thích nghi',limits=(0,1,.05))
        self.vars['fill_holes']=tk.BooleanVar(value=True); self.vars['bright_foreground']=tk.BooleanVar(value=True)
        for text,key in [('Reconstruction (tái tạo để lấp lỗ)','fill_holes'),('Đối tượng sáng trên nền tối','bright_foreground')]:
            widget=ttk.Checkbutton(sidebar,text=text,variable=self.vars[key]); widget.pack(anchor='w',padx=13,pady=4)
            self.input_widgets.append((widget,'normal'))
        tk.Label(sidebar,text='Vùng nhỏ hơn diện tích tối thiểu sẽ bị loại.\nCuộn để xem thêm tham số.',justify='left',bg=PANEL,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=15,pady=12)
        self.button(sidebar_footer,'▶  Phân đoạn ảnh',self.segment,accent=True,fill='x',padx=15,pady=(12,5))
        settings=ttk.Frame(sidebar_footer,style='Panel.TFrame'); settings.pack(fill='x',padx=15,pady=(4,12))
        self.button(settings,'Lưu cấu hình',self.save_config,side='left',fill='x',expand=True,padx=(0,3))
        self.button(settings,'Nạp cấu hình',self.load_config,side='left',fill='x',expand=True)
        self.button(settings,'Mặc định',self.reset_config,side='left',padx=(3,0))
        content=ttk.Frame(body); content.pack(side='left',fill='both',expand=True)
        cards=ttk.Frame(content); cards.pack(fill='x',pady=(0,12))
        self.cards={}
        for key,title in [('objects','ĐỐI TƯỢNG ĐÃ TÁCH'),('markers','MARKER (ĐIỂM KHỞI TẠO)'),('time','THỜI GIAN XỬ LÝ'),('f1','F1 (CHẤT LƯỢNG TÁCH)')]:
            box=tk.Frame(cards,bg=PANEL); box.pack(side='left',fill='both',expand=True,padx=(0,8))
            tk.Frame(box,bg=VIOLET if key=='f1' else ACCENT,height=3).pack(fill='x')
            tk.Label(box,text=title,bg=PANEL,fg=MUTED,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=14,pady=(10,2))
            var=tk.StringVar(value='—'); self.cards[key]=var
            tk.Label(box,textvariable=var,bg=PANEL,fg=ACCENT,font=('Segoe UI',22,'bold')).pack(anchor='w',padx=14,pady=(0,10))
            if key=='f1': Tooltip(box,'F1 từ 0 đến 1; cao hơn tốt hơn. Cần nhãn đúng; dấu — nghĩa là chưa có dữ liệu đánh giá, không phải điểm 0.')
        self.file_label=tk.StringVar(value='Chưa có ảnh · TIFF / PNG / JPG / BMP')
        tk.Label(content,textvariable=self.file_label,bg=BG,fg=MUTED,anchor='w',font=('Segoe UI',10)).pack(fill='x',pady=(0,8))
        self.notice=tk.StringVar(value='Bắt đầu với ảnh mẫu có nhãn. Tách vùng theo độ sáng và hình dạng; ảnh nền đơn giản thường phù hợp hơn.')
        notice_label=tk.Label(content,textvariable=self.notice,bg='#1b3044',fg='#c5dfef',anchor='w',justify='left',padx=12,pady=8,wraplength=900,font=('Segoe UI',9))
        notice_label.pack(fill='x',pady=(0,8))
        content.bind('<Configure>',lambda e:notice_label.configure(wraplength=max(300,e.width-30)))
        self.tabs=ttk.Notebook(content); self.tabs.pack(fill='both',expand=True)
        self.work=ttk.Frame(self.tabs); self.comp=ttk.Frame(self.tabs); self.batch=ttk.Frame(self.tabs); self.help=ttk.Frame(self.tabs)
        self.research=ttk.Frame(self.tabs); self.archive=ttk.Frame(self.tabs)
        for tab,name in [(self.work,'Phân đoạn'),(self.comp,'Fiji & đánh giá'),(self.batch,'Benchmark (đo so sánh)'),(self.research,'Nghiên cứu'),(self.archive,'Phiên đã lưu'),(self.help,'Hướng dẫn')]: self.tabs.add(tab,text=name)
        bar=ttk.Frame(self.work); bar.pack(fill='x',pady=8)
        self.view=ChoiceVar(self.root,group='view',value='Tổng quan 6 bước')
        chooser=ttk.Combobox(bar,textvariable=self.view,state='readonly',width=32,values=self.view.display_values)
        chooser.pack(side='left'); chooser.bind('<<ComboboxSelected>>',lambda _:self.draw())
        Tooltip(chooser,'Chọn từng ảnh trung gian để kiểm tra thuật toán. Marker được khoanh tròn cho dễ nhìn; dữ liệu TIFF giữ nguyên kích thước thực.')
        self.button(bar,'Xuất toàn bộ kết quả',self.export,side='right',padx=3)
        self.button(bar,'Mở thư mục kết quả',self.open_output,side='right',padx=3)
        markerbar=ttk.Frame(self.work); markerbar.pack(fill='x',pady=3)
        ttk.Checkbutton(markerbar,text='Sửa marker (điểm khởi tạo)',variable=self.marker_edit).pack(side='left')
        self.button(markerbar,'Áp dụng marker',self.apply_markers,side='left',padx=5)
        self.button(markerbar,'Marker tự động',self.reset_markers,side='left',padx=3)
        self.button(markerbar,'Xem bảng đối tượng',self.show_objects,side='right',padx=3)
        self.fig=Figure(figsize=(10,5.4),facecolor=BG,layout='constrained')
        self.canvas=FigureCanvasTkAgg(self.fig,master=self.work); self.canvas.get_tk_widget().pack(fill='both',expand=True)
        self.canvas.mpl_connect('button_press_event',self.inspect_object)
        nav=ttk.Frame(self.work); nav.pack(fill='x',pady=4)
        self.toolbar=NavigationToolbar2Tk(self.canvas,nav,pack_toolbar=False)
        self.nav_buttons={}
        for key,text in [('home','Khôi phục góc nhìn'),('zoom','Zoom (phóng to)'),('pan','Pan (di chuyển)'),('save_figure','Lưu hình…')]:
            b=ttk.Button(nav,text=text,command=lambda k=key:self.navigate(k))
            b.pack(side='left',padx=(0,5)); self.nav_buttons[key]=b
        self.object_info=tk.StringVar(value='Chọn một vật thể trên ảnh kết quả để xem diện tích và tâm.')
        object_label=tk.Label(self.work,textvariable=self.object_info,bg=BG,fg=MUTED,anchor='w',wraplength=1000)
        object_label.pack(side='bottom',fill='x',pady=5,before=self.canvas.get_tk_widget())
        nav.pack_configure(side='bottom',before=self.canvas.get_tk_widget())
        refbar=ttk.Frame(self.comp); refbar.pack(fill='x',pady=8)
        self.button(refbar,'Ground truth (nạp nhãn đúng)…',self.open_truth,side='left',padx=3)
        self.button(refbar,'Chạy Fiji / MorphoLibJ',self.fiji,accent=True,side='left',padx=3)
        self.button(refbar,'Quy trình Fiji độc lập',lambda:self.fiji(native=True),side='left',padx=3)
        refoptions=ttk.Frame(self.comp); refoptions.pack(fill='x',pady=(0,5))
        self.button(refoptions,'Nạp kết quả Fiji…',self.import_reference,side='left',padx=3)
        self.button(refoptions,'Thư mục Fiji…',self.choose_fiji,side='left',padx=3)
        self.fiji_home=r'C:\Tools\Fiji'
        self.cfig=Figure(figsize=(10,3),facecolor=BG,layout='constrained')
        self.ccanvas=FigureCanvasTkAgg(self.cfig,master=self.comp)
        metric_panel=ttk.Frame(self.comp); metric_panel.pack(side='bottom',fill='x')
        metric_box=ttk.Frame(metric_panel); metric_box.pack(fill='x',pady=6)
        self.metric_tree=ttk.Treeview(metric_box,columns=('metric','python','fiji'),show='headings',height=5)
        metric_scroll=ttk.Scrollbar(metric_box,command=self.metric_tree.yview)
        self.metric_tree.configure(yscrollcommand=metric_scroll.set)
        metric_scroll.pack(side='right',fill='y')
        for col,text,width in [('metric','Chỉ số đánh giá',330),('python','Python → nhãn đúng',190),('fiji','Fiji → nhãn đúng',190)]:
            self.metric_tree.heading(col,text=text); self.metric_tree.column(col,width=width,anchor='w')
        self.metric_tree.pack(fill='x',expand=True)
        self.comparison_note=tk.StringVar(value='Ground truth (nhãn đúng) đánh giá độ đúng; Fiji kiểm chứng triển khai.')
        tk.Label(metric_panel,textvariable=self.comparison_note,bg=BG,fg=MUTED,wraplength=1000,justify='left').pack(fill='x',pady=6)
        tk.Label(metric_panel,text='IoU / Dice / F1 / PQ: cao hơn tốt hơn (0–1). Sai số đếm / Split / Merge: thấp hơn tốt hơn.',
            bg=BG,fg=MUTED,wraplength=1000,justify='left').pack(fill='x',pady=(0,6))
        self.ccanvas.get_tk_widget().pack(fill='both',expand=True)
        self.build_batch()
        self.build_research()
        self.build_archive()
        self.build_help()
        footer=ttk.Frame(self.root); footer.pack(side='bottom',fill='x',padx=22,pady=10,before=body)
        self.progress=ttk.Progressbar(footer,mode='indeterminate',length=110)
        self.progress.pack(side='right',padx=(10,0))
        self.status=tk.StringVar()
        tk.Label(footer,textvariable=self.status,bg=BG,fg=MUTED,anchor='w',font=('Segoe UI',9),wraplength=1100,justify='left').pack(side='left',fill='x',expand=True)
        self.draw(); self.draw_compare()

    def build_batch(self):
        options=ttk.Frame(self.batch); options.pack(fill='x',pady=10)
        self.dataset=ChoiceVar(self.root,group='dataset',value='synthetic')
        self.split=ChoiceVar(self.root,group='split',value='validation'); self.limit=tk.StringVar(value='6'); self.repeats=tk.StringVar(value='3')
        for i,(title,var) in enumerate([('Dataset (bộ ảnh)',self.dataset),('Split (phần dữ liệu)',self.split),('Số ảnh',self.limit),('Lặp đo',self.repeats)]):
            group=ttk.Frame(options); group.grid(row=0,column=i,sticky='ew',padx=4)
            options.columnconfigure(i,weight=2 if i<2 else 1)
            ttk.Label(group,text=title,background=BG).pack(anchor='w',pady=(0,4))
            if i<2: widget=ttk.Combobox(group,textvariable=var,values=var.display_values,state='readonly',width=25)
            else: widget=ttk.Spinbox(group,textvariable=var,from_=1,to=200 if i==2 else 20,width=6)
            widget.pack(fill='x'); self.input_widgets.append((widget,'readonly' if i<2 else 'normal'))
        actions=ttk.Frame(self.batch); actions.pack(fill='x',pady=4)
        self.button(actions,'Chạy 4 phương pháp × 2 bản',self.benchmark,accent=True,side='left',padx=3)
        self.button(actions,'Khảo sát h · hmax (lọc cực đại)',self.sweep,side='left',padx=3)
        dataactions=ttk.Frame(self.batch); dataactions.pack(fill='x',pady=4)
        self.button(dataactions,'Chuẩn bị BBBC039',self.prepare_real,side='left',padx=3)
        self.button(dataactions,'Xử lý thư mục ảnh…',self.batch_folder,side='left',padx=3)
        tk.Label(self.batch,text='Benchmark (đo so sánh) không tính thời gian đọc/ghi và tính chỉ số; warm-up (chạy làm nóng) một lượt. Chọn tham số trên validation (tập chọn tham số).',
            bg=BG,fg=MUTED,wraplength=980,justify='left').pack(fill='x',pady=8)
        self.bfig=Figure(figsize=(10,3.8),facecolor=BG,layout='constrained')
        ax=self.bfig.subplots(); ax.axis('off')
        ax.text(.5,.6,'So sánh độ đúng và tốc độ',ha='center',color=INK,fontsize=16,transform=ax.transAxes)
        ax.text(.5,.4,'Chọn bộ ảnh → Chạy 4 phương pháp × 2 bản',ha='center',color=MUTED,fontsize=11,transform=ax.transAxes)
        self.bcanvas=FigureCanvasTkAgg(self.bfig,master=self.batch); self.bcanvas.get_tk_widget().pack(fill='both',expand=True)
        self.log=tk.Text(self.batch,height=6,bg=PANEL,fg=INK,insertbackground=INK,font=('Consolas',9),relief='flat',wrap='word')
        self.log.pack(side='bottom',fill='x',pady=6,before=self.bcanvas.get_tk_widget())

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

    def parameters_changed(self,*_):
        if not hasattr(self,'notice'): return
        try: params=self.parameters()
        except (ValueError,tk.TclError):
            self.notice.set('Tham số đang nhập chưa hợp lệ. Hoàn tất giá trị trước khi bấm Phân đoạn.'); return
        if self.result is not None and asdict(params)!=asdict(self.result.params):
            self.notice.set('Đã đổi tham số · Hình và số liệu vẫn thuộc lần chạy trước. Bấm Phân đoạn để cập nhật.')
        elif self.marker_dirty:
            self.notice.set('Marker (điểm khởi tạo) chưa áp dụng. Bấm Áp dụng marker để cập nhật kết quả.')
        elif self.result is not None:
            self.notice.set(result_notice(self.result,self.truth is not None))

    def sync_navigation(self):
        mode=getattr(self.toolbar.mode,'name','NONE').lower()
        for key in ('zoom','pan'):
            self.nav_buttons[key].configure(style='Accent.TButton' if key==mode else 'TButton')

    def navigate(self,key):
        if key in ('zoom','pan') and self.marker_edit.get(): self.marker_edit.set(False)
        getattr(self.toolbar,key)()
        self.sync_navigation()

    def marker_mode_changed(self,*_):
        if self.marker_edit.get():
            mode=getattr(self.toolbar.mode,'name','NONE')
            if mode=='ZOOM': self.toolbar.zoom()
            elif mode=='PAN': self.toolbar.pan()
            self.object_info.set('Sửa marker (điểm khởi tạo): nhấp trái thêm trong vùng tiền cảnh; nhấp phải xóa điểm gần nhất.')
        else: self.object_info.set('Chọn một vật thể trên ảnh kết quả để xem diện tích và tâm.')
        self.sync_navigation(); self.draw()

    def set_busy_controls(self,busy):
        for widget,state in getattr(self,'input_widgets',[]): widget.configure(state='disabled' if busy else state)
        progress=getattr(self,'progress',None)
        if progress is not None:
            if busy: progress.start(15)
            else: progress.stop(); progress.configure(value=0)

    def require_current_result(self,allow_marker_edits=False):
        if self.result is None:
            self.error('Hãy chạy phân đoạn trước.'); return False
        try: params=self.parameters()
        except (ValueError,tk.TclError) as exc:
            self.error('Tham số chưa hợp lệ: '+str(exc)); return False
        if asdict(params)!=asdict(self.result.params):
            self.error('Tham số đã đổi nhưng kết quả vẫn thuộc lần chạy trước. Bấm Phân đoạn để cập nhật trước.'); return False
        if self.marker_dirty and not allow_marker_edits:
            self.error('Marker (điểm khởi tạo) chưa áp dụng. Áp dụng hoặc khôi phục marker tự động trước.'); return False
        return True

    def job(self,function,done,message):
        if self.busy: return
        self.busy=True; self.status.set(message)
        for b in self.actions: b.configure(state='disabled')
        self.set_busy_controls(True)
        from .tasks import Cancellation,task_scope,Cancelled
        self.token=Cancellation(); self.stop_button.configure(state='normal')
        def worker():
            try:
                with task_scope(self.token): value=function()
                self.events.put(('done',(done,value)))
            except Cancelled as exc: self.events.put(('cancelled',str(exc)))
            except Exception as exc: self.events.put(('error',(str(exc),traceback.format_exc())))
        self.worker=threading.Thread(target=worker,daemon=True); self.worker.start()

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='log':
                    self.log.insert('end',value+'\n'); self.log.see('end'); self.status.set(value)
                else:
                    self.busy=False
                    self.set_busy_controls(False)
                    self.stop_button.configure(state='disabled')
                    for b in self.actions: b.configure(state='normal')
                    if self.closing: continue
                    if kind=='cancelled': self.status.set(value)
                    elif kind=='done':
                        callback,result=value
                        try: callback(result)
                        except Exception as exc: self.error(str(exc))
                    else:
                        self.log.insert('end',value[1]+'\n'); self.error(value[0])
        except queue.Empty: pass
        if self.closing:
            if self.worker is None or not self.worker.is_alive(): self.root.destroy(); return
        self.root.after(100,self.poll)

    def cancel(self):
        if self.token is not None: self.token.cancel()
        self.status.set('Đang dừng; chờ bước tính hiện tại và thu hồi tiến trình Fiji…')

    def close(self):
        self.closing=True
        if self.busy: self.cancel()
        else: self.root.destroy()

    def error(self,message):
        self.status.set('Chưa hoàn tất · '+message[:150]); messagebox.showerror('MorphoLab',message,parent=self.root)

    def set_image(self,path,truthpath=None):
        try:
            image=read_image(path)
            truth=read_labels(truthpath,image.shape) if truthpath else None
        except Exception as exc: self.error(str(exc)); return
        self.image=image; self.imagepath=Path(path); self.truth=truth
        self.result=None; self.reference=None; self.diff=None
        self.comparison_note.set('Ground truth (nhãn đúng) đánh giá độ đúng; Fiji kiểm chứng triển khai.')
        self.manual_markers=None; self.marker_dirty=False; self.marker_edit.set(False); self.last_output=None
        self.file_label.set(f'{self.imagepath.name}  ·  {image.shape[1]} × {image.shape[0]} pixel  ·  '+('Có nhãn đúng' if truth is not None else 'Chưa có nhãn đúng'))
        self.notice.set('Ảnh đã nạp. Chọn phương pháp rồi bấm Phân đoạn; F1 chỉ tính khi có ground truth (nhãn đúng).')
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
        self.comparison_note.set('Chưa chạy Fiji cho kết quả này. Ground truth (nhãn đúng) dùng để tính độ chính xác.')
        self.marker_dirty=False
        self.manual_markers=result.stages['markers'].copy()
        self.cards['objects'].set(str(np.unique(result.labels[result.labels>0]).size))
        self.cards['markers'].set(str(np.unique(result.stages['markers'][result.stages['markers']>0]).size))
        self.cards['time'].set(f'{result.timings["total"]:.3f} s')
        self.draw(); self.draw_compare(); self.refresh_metrics()
        self.notice.set(result_notice(result,self.truth is not None))
        self.status.set(f'Hoàn tất · {caption("engine",result.params.engine)} / {caption("mode",result.params.mode)} · Ngưỡng={result.threshold:.4f}')

    def draw(self):
        self.toolbar.update()
        self.fig.clear()
        if self.image is None:
            ax=self.fig.add_subplot(); ax.set_facecolor(BG); ax.axis('off')
            ax.text(.5,.62,'Phân đoạn từng đối tượng',ha='center',color=INK,fontsize=23,transform=ax.transAxes)
            ax.text(.5,.46,'Mở ảnh mẫu có nhãn → Phân đoạn → Kiểm chứng Fiji',ha='center',color=MUTED,fontsize=12,transform=ax.transAxes)
        elif self.result is None:
            ax=self.fig.add_subplot(); self.show(ax,self.image,'Ảnh đầu vào','gray')
        else:
            titles={'gray':'01 · Ảnh đầu vào','binary':'02 · Binary (ảnh sau ngưỡng)','mask':'03 · Mask (vùng tiền cảnh)',
                'distance':'04 · Distance (khoảng cách tới nền)','markers':'05 · Marker (điểm khởi tạo)','labels':'06 · Labels (vật thể đã tách)'}
            keys=['gray','binary','mask','distance','markers','labels'] if self.view.get()=='Tổng quan 6 bước' else [self.view.get()]
            for i,key in enumerate(keys):
                ax=self.fig.add_subplot(2,3,i+1) if len(keys)>1 else self.fig.add_subplot()
                array=self.result.stages[key]
                if key=='labels': array=overlay(self.image,array)
                elif key in ('markers','components'):
                    values=self.manual_markers if key=='markers' and self.marker_edit.get() and self.manual_markers is not None else array
                    array=overlay(self.image,values) if key=='markers' else label_rgb(values)
                self.show(ax,array,titles.get(key,caption('view',key)),'magma' if key in ('distance','elevation') else 'gray')
                if key=='labels' and not self.result.labels.any():
                    ax.text(.5,.5,'Không có đối tượng\nKiểm tra ngưỡng / diện tích tối thiểu',ha='center',va='center',
                        color='#ffe0a3',fontsize=10,transform=ax.transAxes,bbox={'facecolor':BG,'alpha':.88,'edgecolor':'none','pad':12})
                if key=='markers':
                    props=object_table(values,self.image)
                    if not props.empty: ax.scatter(props['centroid-1'],props['centroid-0'],s=35,facecolors='none',edgecolors=ACCENT)
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
        if getattr(getattr(self,'toolbar',None),'mode',''): return
        y,x=int(event.ydata+.5),int(event.xdata+.5)
        if not (0<=y<self.result.labels.shape[0] and 0<=x<self.result.labels.shape[1]): return
        if self.marker_edit.get() and not self.busy:
            if self.manual_markers is None: self.manual_markers=self.result.stages['markers'].copy()
            if event.button==1:
                if not self.result.stages['mask'][y,x]: self.status.set('Đặt marker (điểm khởi tạo) bên trong mask (vùng tiền cảnh).'); return
                if self.manual_markers[y,x]: return
                self.manual_markers[y,x]=int(self.manual_markers.max(initial=0))+1
            elif event.button==3:
                positions=np.argwhere(self.manual_markers>0)
                if not positions.size: return
                nearest=positions[np.argmin(((positions-[y,x])**2).sum(1))]
                label=self.manual_markers[tuple(nearest)]
                self.manual_markers[self.manual_markers==label]=0
            else: return
            self.marker_dirty=True
            self.view.set('markers'); self.draw()
            self.parameters_changed()
            self.status.set('Marker đã sửa · Nhấn Áp dụng marker để tính lại Watershed.'); return
        idx=int(self.result.labels[y,x])
        if not idx: self.object_info.set('Vị trí đang chọn thuộc nền.'); return
        row=object_table(self.result.labels,self.image).set_index('label').loc[idx]
        self.object_info.set(f'Đối tượng #{idx} · Diện tích {row["area"]:.0f} pixel² · Tâm (x={row["centroid-1"]:.1f}, y={row["centroid-0"]:.1f}) · Đường kính tương đương {row["equivalent_diameter_area"]:.1f} pixel')

    def open_truth(self):
        if self.image is None: self.error('Hãy chọn ảnh trước'); return
        name=filedialog.askopenfilename(parent=self.root,title='Nhãn 2D số nguyên; nền 0; mỗi vật thể một ID',filetypes=[('Labels','*.tif *.tiff *.png')])
        if not name: return
        try:
            truth=read_labels(name,self.image.shape)
            self.truth=truth; self.refresh_metrics(); self.parameters_changed()
            self.file_label.set(f'{self.imagepath.name if self.imagepath else "Phiên đã lưu"} · {self.image.shape[1]} × {self.image.shape[0]} pixel · Có nhãn đúng')
        except Exception as exc: self.error(str(exc))

    def refresh_metrics(self):
        self.metric_tree.delete(*self.metric_tree.get_children())
        self.cards['f1'].set('—')
        if self.result is None or self.truth is None: return
        metrics=evaluate(self.truth,self.result.labels)
        self.cards['f1'].set(f'{metrics["object_f1"]:.3f}')
        reference=evaluate(self.truth,self.reference) if self.reference is not None else {}
        names={'foreground_iou':'IoU (độ khớp vùng tiền cảnh)','foreground_dice':'Dice (độ trùng vùng tiền cảnh)',
            'object_f1':'F1 (chất lượng tách, IoU ≥ 0.5)','panoptic_quality':'PQ (tách đúng và khớp hình)',
            'count_absolute_error':'Sai số đếm','split_objects':'Split (vật thể bị chia thừa)',
            'merge_objects':'Merge (vật thể bị gộp)','true_objects':'Số đối tượng theo nhãn đúng'}
        for key,title in names.items():
            fmt=lambda val:f'{val:.4f}' if isinstance(val,float) else str(val)
            self.metric_tree.insert('',tk.END,values=(title,fmt(metrics[key]),fmt(reference[key]) if key in reference else '—'))

    def output_folder(self,prefix):
        return ROOT/'outputs'/f'{prefix}_{datetime.now():%Y%m%d_%H%M%S_%f}'

    def fiji(self,native=False):
        if not self.require_current_result(): return
        if self.result.params.mode=='ccl': self.error('CCL chưa phải Watershed. Hãy chọn raw/hmax/adaptive rồi phân đoạn lại để kiểm chứng Watershed.'); return
        from .fiji import run_reference
        folder=self.output_folder('fiji'); result=self.result; truth=self.truth; home=self.fiji_home
        def done(value):
            labels,stats,self.diff=value; self.reference=labels; self.last_output=folder
            self.draw_compare(); self.refresh_metrics(); self.tabs.select(self.comp)
            score=stats['comparison']['matched_pixel_agreement_foreground_union']
            protocol='Quy trình Fiji độc lập (phần tử vuông, ngưỡng Otsu, khoảng cách ImageJ)' if native else 'Cùng địa hình, marker (điểm khởi tạo), mask (vùng tiền cảnh); có thể khác ở vùng đồng mức'
            self.comparison_note.set(f'Đồng thuận pixel sau ghép ID: {score:.2%}. {protocol}. fiji_metrics.csv do Java/ImageJ tính.')
            self.status.set('Đã chạy MorphoLibJ thật · '+str(folder))
        self.job(lambda:run_reference(result,folder,truth,home,native=native),done,'Đang gọi Fiji / MorphoLibJ bằng Java…')

    def choose_fiji(self):
        path=filedialog.askdirectory(parent=self.root,title='Chọn thư mục Fiji chứa jars, plugins, java')
        if path: self.fiji_home=path; self.status.set('Fiji: '+path)

    def import_reference(self):
        if not self.require_current_result(): return
        name=filedialog.askopenfilename(parent=self.root,title='Ảnh nhãn xuất từ Fiji',filetypes=[('Labels','*.tif *.tiff *.png')])
        if not name: return
        try:
            reference=read_labels(name,self.result.labels.shape)
            stats,diff=compare_labels(reference,self.result.labels)
            self.reference=reference; self.diff=diff
            self.draw_compare(); self.refresh_metrics()
            self.comparison_note.set('Đồng thuận pixel sau ghép ID: '+f'{stats["matched_pixel_agreement_foreground_union"]:.2%}')
        except Exception as exc: self.error(str(exc))

    def export(self):
        if not self.require_current_result(): return
        name=filedialog.askdirectory(parent=self.root,title='Chọn thư mục cha lưu kết quả')
        if not name: return
        folder=Path(name)/self.output_folder('run').name
        result=self.result; truth=self.truth; reference=self.reference; source=self.imagepath
        image=self.image.copy()
        def work():
            from .sessions import save_session
            return save_session(result,image,folder,truth,reference,source)
        def done(path):
            self.last_output=path; self.refresh_history()
            self.status.set('Đã lưu phiên có thể mở lại và phiếu report.html: '+str(path))
        self.job(work,done,'Đang xuất kết quả…')

    def open_output(self):
        path=self.last_output or ROOT/'outputs'; path.mkdir(parents=True,exist_ok=True)
        os.startfile(str(path))

    def save_config(self):
        try: params=self.parameters()
        except Exception as exc: self.error(str(exc)); return
        name=filedialog.asksaveasfilename(parent=self.root,defaultextension='.json',initialdir=str(ROOT/'configs'),filetypes=[('JSON','*.json')])
        if name: write_json(name,asdict(params)); self.status.set('Đã lưu tham số: '+name)

    def reset_config(self):
        for key,value in asdict(Parameters()).items(): self.vars[key].set(value)
        self.status.set('Đã khôi phục cấu hình mặc định · Bấm Phân đoạn để chạy lại.')

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
            modes=[caption('mode',m).replace(' (','\n(') for m in part['mode']]
            a.plot(modes,part.object_f1,'o-',label=caption('engine',engine))
            b.plot(modes,part.seconds_median,'o-',label=caption('engine',engine))
        for ax in (a,b): ax.tick_params(axis='x',labelsize=8)
        a.set_ylim(0,1.05); a.set_title('F1 (chất lượng tách)',color=INK); b.set_title('Thời gian (giây)',color=INK)
        for ax in (a,b): ax.legend(facecolor=PANEL,edgecolor=BORDER,labelcolor=INK,fontsize=8)
        self.bcanvas.draw_idle()
        for row in summary.itertuples():
            self.log.insert('end',f'{caption("engine",row.engine)} · {caption("mode",row.mode)} · {row.images} ảnh · F1 (chất lượng tách)={row.object_f1:.3f} · {row.seconds_median:.3f} giây\n')
        self.status.set('Benchmark hoàn tất · '+str(folder))

    def sweep(self):
        try: manifest,limit,repeats,params=self.experiment_inputs()
        except Exception as exc: self.error(str(exc)); return
        from .benchmark import sweep
        folder=self.output_folder('sweep')
        def done(table):
            self.last_output=folder
            for row in table.itertuples(): self.log.insert('end',f'h (độ cao cực đại)={row.h:g} · F1 (chất lượng tách)={row.object_f1:.3f}\n')
            self.status.set('Đã khảo sát hmax trên validation (tập chọn tham số) · Nạp selected_parameters.json để sử dụng; chưa đánh giá test (tập cuối).')
        self.job(lambda:sweep(manifest,folder,params,limit=limit,progress=lambda s:self.events.put(('log',s))),done,'Đang khảo sát h trên validation…')

    def batch_folder(self):
        try: params=self.parameters()
        except Exception as exc: self.error(str(exc)); return
        name=filedialog.askdirectory(parent=self.root,title='Chọn thư mục ảnh; nhãn đúng tùy chọn: tênảnh_gt.tif')
        if not name: return
        from .benchmark import process_folder
        folder=self.output_folder('batch')
        def done(frame):
            self.last_output=folder
            for row in frame.to_dict('records'):
                if row['status']=='ok':
                    score=row.get('object_f1',float('nan'))
                    detail=f'{row["objects"]:g} đối tượng · '+(f'F1 (chất lượng tách)={score:.3f}' if np.isfinite(score) else 'Chưa có nhãn đúng')
                else: detail='Lỗi: '+row['error']
                self.log.insert('end',f'{row["image"]} · {detail}\n')
            errors=int((frame.status=='error').sum())
            self.status.set(f'Xong {len(frame)} ảnh · {errors} lỗi · '+str(folder))
        self.job(lambda:process_folder(name,folder,params,progress=lambda s:self.events.put(('log',s))),done,'Đang xử lý thư mục ảnh…')

    def apply_markers(self):
        if not self.require_current_result(allow_marker_edits=True): return
        if self.manual_markers is None: self.error('Phân đoạn tự động trước khi sửa marker'); return
        p=self.result.params; image=self.image.copy(); markers=self.manual_markers.copy()
        self.job(lambda:run(image,p,manual_markers=markers),self.segment_done,'Đang tính Watershed với marker thủ công…')

    def reset_markers(self):
        self.marker_edit.set(False)
        if self.result is not None:
            self.segment()

    def show_objects(self):
        if self.result is None: self.error('Hãy phân đoạn trước'); return
        table=object_table(self.result.labels,self.image)
        window=tk.Toplevel(self.root); window.title('Bảng đối tượng · đơn vị pixel / pixel²'); window.geometry('1100x500')
        columns=list(table.columns)
        tree=ttk.Treeview(window,columns=columns,show='headings')
        xs=ttk.Scrollbar(window,orient='horizontal',command=tree.xview)
        ys=ttk.Scrollbar(window,orient='vertical',command=tree.yview)
        tree.configure(xscrollcommand=xs.set,yscrollcommand=ys.set)
        xs.pack(side='bottom',fill='x'); ys.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        for col in columns: tree.heading(col,text=OBJECT_COLUMNS.get(col,col)); tree.column(col,width=220,stretch=False)
        for row in table.itertuples(index=False,name=None): tree.insert('',tk.END,values=[f'{v:.3f}' if isinstance(v,float) else v for v in row])

    def build_research(self):
        bar=ttk.Frame(self.research); bar.pack(fill='x',pady=10)
        self.study_kind=ChoiceVar(self.root,group='study',value='compare')
        ttk.Label(bar,text='Kế hoạch').pack(side='left',padx=5)
        widget=ttk.Combobox(bar,textvariable=self.study_kind,values=self.study_kind.display_values,state='readonly',width=29)
        widget.pack(side='left'); self.input_widgets.append((widget,'readonly'))
        self.button(bar,'Chạy kế hoạch',self.run_study,accent=True,side='left',padx=8)
        self.button(bar,'HTML (phiếu kết quả)',self.open_report,side='left',padx=3)
        tk.Label(self.research,text='Chọn bộ ảnh, phần dữ liệu, số ảnh và lặp đo ở tab Benchmark (đo so sánh). Chạy tuần tự từng ảnh.\nCompare (so sánh bốn cách) · Ablation (bỏ từng bước) · Robustness (thử nhiễu, mờ với seed / số khởi tạo cố định).',
            bg=BG,fg=MUTED,justify='left',wraplength=900).pack(anchor='w',padx=8,pady=8)
        columns=['variant','images','object_f1','ci_low','ci_high','foreground_iou','count_mae','pipeline_seconds','watershed_seconds','process_seconds','native_seconds_with_io']
        box=ttk.Frame(self.research); box.pack(fill='both',expand=True)
        self.study_table=ttk.Treeview(box,columns=columns,show='headings')
        xs=ttk.Scrollbar(box,orient='horizontal',command=self.study_table.xview)
        ys=ttk.Scrollbar(box,orient='vertical',command=self.study_table.yview)
        self.study_table.configure(xscrollcommand=xs.set,yscrollcommand=ys.set)
        xs.pack(side='bottom',fill='x'); ys.pack(side='right',fill='y'); self.study_table.pack(fill='both',expand=True)
        for col in columns:
            title={'variant':'Cấu hình và ý nghĩa','images':'Số ảnh','object_f1':'F1 (chất lượng tách)','ci_low':'CI 95% (cận thấp)','ci_high':'CI 95% (cận cao)',
                'foreground_iou':'IoU (khớp tiền cảnh)','count_mae':'Sai số đếm trung bình','pipeline_seconds':'Python (toàn quy trình, s)',
                'watershed_seconds':'Watershed (bước tách, s)','process_seconds':'Tiến trình Fiji (s)','native_seconds_with_io':'Fiji riêng + đọc/ghi (s)'}[col]
            self.study_table.heading(col,text=title); self.study_table.column(col,width=270 if col=='variant' else 165,stretch=False)
        tk.Label(self.research,text='Fiji shared (chung đầu vào) đo riêng Watershed. Native (quy trình riêng) có thời gian đọc/ghi ảnh.\nCI (khoảng ước lượng) mô tả biến thiên giữa ảnh; các loại thời gian có phạm vi đo khác nhau.',
            bg=BG,fg=MUTED,justify='left',wraplength=900).pack(anchor='w',padx=8,pady=12)

    def run_study(self):
        try: manifest,limit,repeats,params=self.experiment_inputs()
        except Exception as exc: self.error(str(exc)); return
        from .studies import study
        kind=self.study_kind.get(); split=self.split.get(); home=self.fiji_home; folder=self.output_folder(kind)
        def done(value):
            frame,summary=value; self.last_output=folder
            self.refresh_history()
            self.study_table.delete(*self.study_table.get_children())
            for _,row in summary.iterrows():
                self.study_table.insert('',tk.END,values=[caption('variant',row.get(c,'')) if c=='variant' else self.format_cell(row.get(c,'')) for c in self.study_table['columns']])
            errors=int((frame.status=='error').sum())
            self.status.set(f'Đã xong {caption("study",kind)} · {errors} lỗi · Phiếu HTML và CSV: '+str(folder))
        self.job(lambda:study(manifest,folder,params,kind,split,limit,repeats,fiji_home=home,
            progress=lambda s:self.events.put(('log',s))),done,'Đang chạy kế hoạch nghiên cứu…')

    @staticmethod
    def format_cell(value):
        if value is None: return '—'
        if isinstance(value,(float,np.floating)): return '' if np.isnan(value) else f'{value:.4f}'
        return str(value)

    def build_archive(self):
        bar=ttk.Frame(self.archive); bar.pack(fill='x',pady=10)
        self.button(bar,'Làm mới',self.refresh_history,side='left',padx=3)
        self.button(bar,'Mở phiên đã chọn',self.open_selected_session,side='left',padx=3)
        self.button(bar,'Mở phiên từ thư mục…',self.choose_session,side='left',padx=3)
        self.button(bar,'HTML (phiếu kết quả)',self.open_report,side='left',padx=3)
        cols=['name','type','engine','mode','objects','f1']
        holder=ttk.Frame(self.archive); holder.pack(fill='both',expand=True)
        self.history_table=ttk.Treeview(holder,columns=cols,show='headings')
        xs=ttk.Scrollbar(holder,orient='horizontal',command=self.history_table.xview)
        ys=ttk.Scrollbar(holder,command=self.history_table.yview)
        self.history_table.configure(xscrollcommand=xs.set,yscrollcommand=ys.set)
        xs.pack(side='bottom',fill='x'); ys.pack(side='right',fill='y')
        for col in cols:
            label={'name':'Tên phiên / thí nghiệm','type':'Loại','engine':'Bản cài đặt','mode':'Phương pháp','objects':'Đối tượng / số ảnh','f1':'F1 (nếu có)'}[col]
            width={'name':310,'type':180,'engine':230,'mode':260,'objects':160,'f1':110}[col]
            self.history_table.heading(col,text=label); self.history_table.column(col,width=width,stretch=False)
        self.history_table.pack(fill='both',expand=True)
        self.history_table.bind('<Double-1>',lambda e:self.open_selected_session())
        self.refresh_history()

    def refresh_history(self):
        from .sessions import history
        self.saved_sessions=history(ROOT/'outputs'); self.history_table.delete(*self.history_table.get_children())
        for i,row in enumerate(self.saved_sessions):
            display=dict(row)
            display['engine']=caption('engine',row.get('engine',''))
            display['mode']=caption('study' if row['type']=='study' else 'mode',row.get('mode',''))
            display['type']='study (thí nghiệm)' if row['type']=='study' else 'session (phiên làm việc)'
            self.history_table.insert('',tk.END,iid=str(i),values=[self.format_cell(display.get(c,'')) for c in self.history_table['columns']])

    def choose_session(self):
        path=filedialog.askdirectory(parent=self.root,title='Thư mục phiên đã lưu chứa run.json và input.tif')
        if path: self.restore_session(path)

    def open_selected_session(self):
        selected=self.history_table.selection()
        if selected:
            row=self.saved_sessions[int(selected[0])]
            if row['type']=='session': self.restore_session(row['folder'])
            else:
                import pandas as pd
                path=Path(row['folder'])
                if not (path/'summary.csv').exists(): self.error('Thí nghiệm chưa có dòng hoàn tất để hiển thị'); return
                def done(summary):
                    self.last_output=path; self.study_table.delete(*self.study_table.get_children())
                    for _,r in summary.iterrows():
                        self.study_table.insert('',tk.END,values=[caption('variant',r.get(c,'')) if c=='variant' else self.format_cell(r.get(c,'')) for c in self.study_table['columns']])
                    self.tabs.select(self.research); self.status.set('Đã mở số liệu thí nghiệm: '+str(path))
                self.job(lambda:pd.read_csv(path/'summary.csv'),done,'Đang mở số liệu…')

    def restore_session(self,path):
        from .sessions import load_session
        def done(session):
            self.image=session.image; self.imagepath=Path(session.source) if session.source else None
            self.truth=session.truth; self.marker_edit.set(False); self.segment_done(session.result)
            self.reference=session.reference
            self.diff=compare_labels(self.reference,self.result.labels)[1] if self.reference is not None else None
            for key,value in asdict(session.result.params).items(): self.vars[key].set(value)
            self.last_output=Path(path); self.file_label.set('Phiên đã khôi phục · '+str(path))
            self.draw_compare(); self.refresh_metrics(); self.tabs.select(self.work)
            self.status.set('Đã khôi phục ảnh, nhãn đúng, cấu hình và kết quả; không tính lại.')
        self.job(lambda:load_session(path),done,'Đang mở phiên đã lưu…')

    def open_report(self):
        path=(self.last_output or ROOT/'outputs')/'report.html'
        if path.exists(): os.startfile(str(path))
        else: self.error('Chưa có report.html. Lưu phiên hoặc chạy kế hoạch nghiên cứu trước.')

    def browse_dataset(self):
        window=tk.Toplevel(self.root); window.title('Duyệt ảnh và nhãn đúng'); window.geometry('1050x570')
        controls=ttk.Frame(window); controls.pack(fill='x',padx=10,pady=10)
        dataset=ChoiceVar(self.root,group='dataset',value='bbbc039'); split=ChoiceVar(self.root,group='split',value='validation'); selected=[]
        for var in [dataset,split]:
            ttk.Combobox(controls,textvariable=var,values=var.display_values,state='readonly',width=28).pack(side='left',padx=5)
        cols=['id','split','source']; tree=ttk.Treeview(window,columns=cols,show='headings')
        for col in cols: tree.heading(col,text={'id':'ID (tên ảnh)','split':'Split (phần dữ liệu)','source':'Source (nguồn)'}[col]); tree.column(col,width=600 if col=='id' else 200)
        scroll=ttk.Scrollbar(window,command=tree.yview); tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y'); tree.pack(fill='both',expand=True,padx=10,pady=8)
        def refresh():
            tree.delete(*tree.get_children()); selected.clear()
            manifest=ROOT/'data'/dataset.get()/'manifest.json'
            if not manifest.exists(): messagebox.showinfo('Dataset','Chuẩn bị BBBC039 trong tab Benchmark trước.',parent=window); return
            selected.extend(records(manifest,split.get()))
            for i,(r,_,_) in enumerate(selected): tree.insert('',tk.END,iid=str(i),values=[caption('split',r.get(c,'')) if c=='split' else r.get(c,'') for c in cols])
        def load():
            if self.busy: return
            choice=tree.selection()
            if choice:
                _,image,truth=selected[int(choice[0])]; self.set_image(image,truth); window.destroy()
        ttk.Button(controls,text='Lọc danh sách',command=refresh).pack(side='left',padx=8)
        ttk.Button(controls,text='Mở ảnh + nhãn đúng',command=load).pack(side='left',padx=8)
        tree.bind('<Double-1>',lambda e:load()); refresh()


HELP='''VAI TRÒ TRONG BÀI TẬP LỚN
Trọng tâm: lý thuyết thuật toán → tự cài đặt → kiểm chứng Fiji → thực nghiệm định lượng → báo cáo và slide.
App hỗ trợ thao tác và minh họa; đề bài không bắt buộc giao diện tích hợp hay quy định điểm cộng riêng cho giao diện.

CÁCH CHẠY THÍ NGHIỆM
1. Chọn ảnh mẫu có nhãn hoặc ảnh tế bào BBBC039.
2. Chọn custom (tự cài) hoặc library (thư viện đối chiếu), rồi Phân đoạn.
3. Xem từng ảnh trung gian, phóng to bằng thanh công cụ và chọn vật thể.
4. Tab Fiji & đánh giá: nạp nhãn đúng hoặc chạy MorphoLibJ thật trên máy.
5. Xuất toàn bộ ảnh TIFF, overlay (ảnh chồng kết quả), bảng đối tượng, tham số, metric (chỉ số đánh giá) và môi trường.
6. Benchmark (đo so sánh): chọn dataset (bộ ảnh), split (phần dữ liệu), số ảnh, số lần đo. Chọn tham số trên validation (tập chọn tham số) trước khi đánh giá test (tập cuối).

THUẬT NGỮ THƯỜNG GẶP
Ground truth (nhãn đúng): ảnh có nền 0 và mã số riêng cho từng vật thể, dùng chấm kết quả.
Mask (vùng tiền cảnh): vùng được giữ lại để phân đoạn. Marker / seed (điểm khởi tạo): điểm bắt đầu cho Watershed.
Watershed (phân vùng theo địa hình): lan nhãn từ marker trên địa hình âm của khoảng cách tới nền.
Reconstruction (tái tạo hình thái): lan vùng từ ảnh đánh dấu dưới giới hạn của ảnh mặt nạ.
CI (khoảng ước lượng): mô tả mức biến thiên thống kê giữa các ảnh, không bảo đảm thuật toán đúng mọi ảnh.

ỨNG DỤNG HỢP NHẤT
Bộ ảnh & nhãn: duyệt ảnh và ground truth theo dataset/split.
Nghiên cứu / compare: chạy Python tự cài, thư viện, Fiji chung đầu vào và workflow Fiji độc lập.
Nghiên cứu / ablation: thử bỏ từng bước để đo tác dụng; robustness: thử ảnh nhiễu và mờ có seed.
Xuất toàn bộ kết quả: lưu phiên có thể mở lại cùng report.html. Phiên đã lưu hiển thị các phiên và thí nghiệm.
Sửa marker: nhấp trái thêm một seed trong mask, phải xóa vùng seed gần nhất; nhấn Áp dụng marker. Mỗi thành phần mask phải có marker.
Đánh giá marker thủ công cần ghi rõ đây là kết quả có can thiệp của người dùng, không trộn với benchmark tự động.
Dừng tác vụ: dừng hợp tác tại các điểm kiểm tra; đóng app cũng gửi lệnh dừng và chờ thu hồi tiến trình Fiji.
Mỗi lần chỉ có một công việc nặng trong app. Fiji được gọi khi cần, giới hạn Java heap 512 MB (không phải toàn bộ RAM tiến trình).

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


def launch(smoke=False):
    os.chdir(ROOT)
    if not (ROOT/'data/synthetic/manifest.json').exists(): synthetic(ROOT/'data')
    root=tk.Tk(); app=App(root)
    if smoke:
        root.after(300,app.demo)
        root.after(600,app.segment)
        root.after(45000,app.close)
    root.mainloop()
