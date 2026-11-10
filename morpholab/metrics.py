"""Đánh giá từng đối tượng bằng ghép một-một; ưu tiên số cặp hợp lệ rồi tổng IoU."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from .io import validate_labels


def _overlap(truth, prediction):
    """Lập bảng diện tích giao giữa từng cặp ID, từ đó tính ma trận IoU."""
    truth = validate_labels(truth)
    prediction = validate_labels(prediction, truth.shape)
    # Bổ sung ID nền 0 cả khi toàn ảnh là vật thể.
    gtids = np.unique(np.append(truth,0))
    prids = np.unique(np.append(prediction,0))
    if len(gtids) > 10001 or len(prids) > 10001 or len(gtids)*len(prids) > 20_000_000:
        raise ValueError('Quá nhiều nhãn để ghép cặp; hãy kiểm tra ảnh nhãn hoặc chọn ROI')
    g = np.searchsorted(gtids,truth)
    p = np.searchsorted(prids,prediction)
    hist = np.bincount((g*len(prids)+p).ravel(),minlength=len(gtids)*len(prids)).reshape(len(gtids),len(prids))
    ga, pa = hist.sum(1)[1:], hist.sum(0)[1:]
    inter = hist[1:,1:]
    union = ga[:,None]+pa[None,:]-inter
    iou = np.divide(inter,union,out=np.zeros_like(inter,dtype=float),where=union>0)
    return hist, ga, pa, inter, iou, g, p


def evaluate(truth, prediction, iou_threshold=.5, overlap_fraction=.1):
    """Ghép từng nhãn dự đoán với nhãn đúng tại IoU yêu cầu, tính F1/PQ và lỗi chia/gộp. IoU/Dice tiền cảnh dùng hai mask ID>0; không phụ thuộc màu LUT."""
    if not 0 < iou_threshold <= 1 or not 0 < overlap_fraction <= 1:
        raise ValueError('Ngưỡng IoU và overlap phải nằm trong (0, 1]')
    _, ga, pa, inter, iou, g, p = _overlap(truth,prediction)
    valid = iou >= iou_threshold
    # Ưu tiên số cặp ghép hợp lệ, sau đó mới tối đa tổng IoU.
    row, col = linear_sum_assignment(-(valid*(min(iou.shape,default=0)+1)+iou*valid))
    matched = valid[row,col]
    tp = int(matched.sum()); ng, npred = len(ga),len(pa)
    fp, fn = npred-tp, ng-tp
    f1 = 2*tp/(ng+npred) if ng+npred else 1.
    fg, pred = np.asarray(truth)>0,np.asarray(prediction)>0
    intersection = int(np.count_nonzero(fg & pred))
    union = int(np.count_nonzero(fg | pred))
    total = int(fg.sum()+pred.sum())
    substantial = (inter>0) & (inter >= overlap_fraction*np.minimum(ga[:,None],pa[None,:]))
    return {'foreground_iou':intersection/union if union else 1.,
            'foreground_dice':2*intersection/total if total else 1.,
            'object_precision':tp/npred if npred else float(ng==0),
            'object_recall':tp/ng if ng else float(npred==0),
            'object_f1':f1,'panoptic_quality':float(iou[row[matched],col[matched]].sum())/(tp+.5*fp+.5*fn) if ng+npred else 1.,
            'mean_matched_iou':float(iou[row[matched],col[matched]].mean()) if tp else 0.,
            'true_objects':ng,'predicted_objects':npred,'tp':tp,'fp':fp,'fn':fn,
            'count_absolute_error':abs(ng-npred),'split_objects':int((substantial.sum(1)>1).sum()),
            'merge_objects':int((substantial.sum(0)>1).sum()),'iou_threshold':iou_threshold,
            'split_merge_overlap_fraction':overlap_fraction}


def compare_labels(reference, prediction):
    """Ghép ID để đo mức đồng thuận hai triển khai. Tham chiếu Fiji không thay nhãn đúng."""
    hist, _, _, _, _, g, p = _overlap(reference,prediction)
    row, col = linear_sum_assignment(-hist[1:,1:])
    mapping = np.full(hist.shape[1],-1,dtype=int)
    mapping[0] = 0
    mapping[col+1] = row+1
    disagreement = mapping[p] != g
    union = (g>0)|(p>0)
    score = 1.-float(disagreement[union].mean()) if union.any() else 1.
    return {'matched_pixel_agreement_foreground_union':score,
            'different_pixels':int(disagreement.sum()),
            'note':'Fiji is an implementation reference, not ground truth.'}, disagreement
