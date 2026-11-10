"""Nhãn giao diện tiếng Việt; giữ nguyên khóa cấu hình và định dạng số liệu."""
import tkinter as tk

CHOICES={
 'engine':{'custom':'custom (thuật toán tự cài)','library':'library (thư viện đối chiếu)'},
 'mode':{'ccl':'ccl (đếm vùng liên thông)','raw':'raw (cực đại chưa lọc)',
         'hmax':'hmax (lọc cực đại theo h)','adaptive':'adaptive (ngưỡng h thích nghi)'},
 'operation':{'none':'none (không xử lý)','erosion':'erosion (co ảnh)','dilation':'dilation (giãn ảnh)',
   'opening':'opening (mở ảnh)','closing':'closing (đóng ảnh)','opening_closing':'opening_closing (mở rồi đóng)',
   'opening_reconstruction':'opening_reconstruction (mở tái tạo)'},
 'shape':{'disk':'disk (hình đĩa)','square':'square (hình vuông)','cross':'cross (chữ thập)'},
 'connectivity':{'4':'4 (bốn hướng)','8':'8 (cả đường chéo)'},
 'dataset':{'synthetic':'synthetic (ảnh tổng hợp)','bbbc039':'BBBC039 (ảnh tế bào)'},
 'split':{'validation':'validation (chọn tham số)','test':'test (đánh giá cuối)','training':'training (tập phát triển)'},
 'study':{'compare':'compare (so sánh bốn cách)','ablation':'ablation (bỏ từng bước)',
          'robustness':'robustness (thử nhiễu, mờ)'},
 'variant':{'python-custom':'Python custom (tự cài)','python-library':'Python library (thư viện)',
   'fiji-shared':'Fiji shared (chung đầu vào)','fiji-native':'Fiji native (quy trình riêng)',
   'baseline':'baseline (cấu hình gốc)','no_gaussian':'no_gaussian (bỏ làm trơn)',
   'no_morphology':'no_morphology (bỏ hình thái)','ordinary_opening':'ordinary_opening (mở thường)',
   'no_fill_holes':'no_fill_holes (bỏ lấp lỗ)','raw_markers':'raw_markers (cực đại chưa lọc)',
   'connected_components':'connected_components (đếm vùng)', 'clean':'clean (ảnh gốc)',
   'noise_0.02':'noise 0.02 (nhiễu nhẹ)','noise_0.05':'noise 0.05 (nhiễu vừa)',
   'noise_0.1':'noise 0.1 (nhiễu mạnh)','blur_1':'blur 1 (mờ nhẹ)',
   'blur_2':'blur 2 (mờ vừa)','blur_3':'blur 3 (mờ mạnh)'},
 'view':{'Tổng quan 6 bước':'Tổng quan 6 bước','gray':'gray (ảnh xám gốc)','smoothed':'smoothed (ảnh làm trơn)',
   'binary':'binary (ảnh sau ngưỡng)','erosion':'erosion (ảnh co)','dilation':'dilation (ảnh giãn)',
   'morphology':'morphology (sau hình thái)','mask':'mask (vùng tiền cảnh)',
   'components':'components (vùng liên thông)','distance':'distance (khoảng cách tới nền)',
   'elevation':'elevation (địa hình Watershed)','markers':'markers (điểm khởi tạo)',
   'labels':'labels (nhãn từng vật thể)'}
}


def caption(group,value):
    return CHOICES.get(group,{}).get(str(value),str(value))


class ChoiceVar(tk.StringVar):
    """A readable Tcl value with canonical Python get/set for old configs."""
    def __init__(self,master=None,*,group,value):
        self.group=group
        self.choices=CHOICES[group]
        self.reverse={v:k for k,v in self.choices.items()}
        super().__init__(master=master,value=caption(group,value))

    def get(self):
        value=super().get()
        return self.reverse.get(value,value)

    def set(self,value):
        super().set(caption(self.group,value))

    @property
    def display_values(self): return list(self.choices.values())


class Tooltip:
    def __init__(self,widget,text):
        self.widget=widget; self.text=text; self.window=None; self.timer=None
        widget.bind('<Enter>',self.enter,add='+')
        widget.bind('<Leave>',self.leave,add='+')
        widget.bind('<ButtonPress>',self.leave,add='+')
    def enter(self,event=None): self.timer=self.widget.after(600,self.show)
    def leave(self,event=None):
        if self.timer:
            self.widget.after_cancel(self.timer); self.timer=None
        if self.window:
            self.window.destroy(); self.window=None
    def show(self):
        if not self.widget.winfo_exists(): return
        self.window=tk.Toplevel(self.widget); self.window.wm_overrideredirect(True)
        self.window.geometry(f'+{self.widget.winfo_rootx()+12}+{self.widget.winfo_rooty()+self.widget.winfo_height()+5}')
        tk.Label(self.window,text=self.text,font=('Segoe UI',10),bg='#263a4e',fg='#edf4fa',
                 padx=12,pady=8,wraplength=360,justify='left').pack()


OBJECT_COLUMNS={'label':'ID (mã vật thể)','area':'area (diện tích pixel²)',
 'centroid-0':'centroid-y (tâm dọc)','centroid-1':'centroid-x (tâm ngang)',
 'bbox-0':'bbox (hàng đầu)','bbox-1':'bbox (cột đầu)','bbox-2':'bbox (hàng cuối)',
 'bbox-3':'bbox (cột cuối)','equivalent_diameter_area':'diameter (đường kính tương đương)',
 'eccentricity':'eccentricity (độ thuôn dài)','solidity':'solidity (độ đầy hình)',
 'intensity_mean':'intensity (độ sáng trung bình)'}


def result_notice(result,has_truth):
    """Explain empty masks; a count is an algorithm output, not a semantic fact."""
    import numpy as np
    if not np.any(result.labels):
        count=int(np.count_nonzero(result.stages.get('morphology',False)))
        if result.params.min_area > result.labels.size:
            return f'Không còn đối tượng: diện tích tối thiểu {result.params.min_area:,} lớn hơn toàn ảnh {result.labels.size:,} pixel. Hãy giảm giá trị này (ví dụ 25).'
        if count:
            return 'Không còn đối tượng sau lọc diện tích. Hãy giảm diện tích tối thiểu hoặc kiểm tra mask (vùng tiền cảnh).'
        return 'Chưa tạo được vùng tiền cảnh. Kiểm tra ngưỡng, sáng/tối của đối tượng và bán kính phần tử cấu trúc.'
    if not has_truth:
        return 'Chưa có ground truth (nhãn đúng): chỉ hiển thị số vùng thuật toán tìm được; chưa tính F1 (chất lượng tách).'
    return 'Có ground truth (nhãn đúng) để kiểm tra. F1 đánh giá ảnh này; không bảo đảm mọi ảnh đều được tách đúng.'
