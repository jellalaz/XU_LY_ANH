import fs from 'node:fs/promises';
import {Presentation,PresentationFile} from 'file:///C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {finalizePresentation,applyPresentationChartFont} from 'file:///C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1104.22356/skills/presentations/container_tools/artifact_tool_utils.mjs';
const ROOT='D:/XU_LY_ANH',BUILD=ROOT+'/outputs/presentation_build';
const SKILL='C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1104.22356/skills/presentations';
await fs.mkdir(BUILD,{recursive:true});
await fs.mkdir(ROOT+'/outputs/presentation_delivery',{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const navy='#102D43',teal='#087F8C',gray='#435466';
function text(s,value,x,y,w,h,size=26,bold=false,color=navy){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=value;q.text.style={fontFamily:'Arial',fontSize:size,bold,color};return q;
}
function slide(title,notes){const s=p.slides.add();s.background.fill='#FFFFFF';
 text(s,'PTIT  /  NHÓM 1  /  XỬ LÝ ẢNH',58,26,1000,26,15,true,teal);
 text(s,title,58,76,1160,100,38,true);
 text(s,'Hình thái học & Watershed  •  Kết quả thực nghiệm của dự án',58,672,1080,24,14,false,gray);
 text(s,String(p.slides.items.length).padStart(2,'0'),1170,668,52,30,18,true,teal);
 s.speakerNotes.text=notes;return s;}
function table(s,values,x,y,w,h,widths){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let cell=t.getCell(r,c);cell.fill=r===0?'#E9F1F5':r%2?'#F6F8FA':'#FFFFFF';cell.text.style={fontFamily:'Arial',fontSize:22,bold:r===0,color:navy};}
 t.borders.assign({style:'solid',fill:'#CED9E0',width:1});return t;}
async function picture(s,path,x,y,w,h){const b=await fs.readFile(ROOT+'/'+path);s.images.add({blob:new Uint8Array(b).buffer,contentType:'image/png',alt:'Kết quả phân đoạn từ thực nghiệm của dự án',fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function chart(s,categories,values,x,y,w,h){const c=s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories,series:[{name:'F1 đối tượng',values,fill:teal}],hasLegend:false,dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0000',textStyle:{fontSize:22}},xAxis:{textStyle:{fontSize:21}},yAxis:{min:0,max:1,textStyle:{fontSize:18},majorGridlines:{fill:'#DDE4E9',width:1,style:'solid'}}});applyPresentationChartFont(c,{fontFamily:'Arial'});return c;}
let s=slide('Phân đoạn đối tượng bằng\nhình thái học toán học và Watershed',
 '40 giây. Giới thiệu đề tài nhóm 1. Mục tiêu: hiểu và tự cài đặt các phép hình thái, tạo marker và tách từng vật thể, rồi kiểm chứng bằng Fiji/MorphoLibJ. Đây là xử lý ảnh cổ điển, không huấn luyện mạng học sâu. Ứng dụng chỉ hỗ trợ thao tác; bằng chứng chính là mã nguồn, dữ liệu và báo cáo. Nguồn yêu cầu: đề bài và ảnh phân nhóm do người học cung cấp.');
text(s,'NGHIÊN CỨU  →  CÀI ĐẶT  →  THỰC NGHIỆM  →  ĐÁNH GIÁ',60,224,1150,48,25,true,teal);
text(s,'Python tự cài đặt · Fiji / MorphoLibJ 1.6.5\nĐối chiếu thuật toán và đánh giá theo nhãn đúng',60,310,1100,90,30);
text(s,'Kiều Trường Giang — B23DCCN254\nTrần Đỗ Lan Phương — B23DCCN667\nGiang Thùy Tiên — B23DCCN814\nPhạm Văn Vỹ — B23DCCN954',60,455,1100,146,23,false,gray);
s=slide('Đầu vào là ảnh; đầu ra là từng vùng có nhãn',
 '50 giây. synth_00 có 7 vật thể, gồm 2 cặp chạm nhau. Connected components cho 5 vùng; Watershed với marker phù hợp cho 7. Mỗi đối tượng nhận một ID; có thể đếm và đo diện tích, tâm. Không tự nhận biết tên người, xe hay loại tế bào. Nguồn: outputs/input_output_example; data/synthetic/synth_00.tif và synth_00_gt.tif. Fiji trong hình là kết quả MorphoLibJ thực chạy. F1=1 trên ví dụ không chứng minh mọi ảnh đều tốt.');
await picture(s,'submission/assets/input_output.png',60,183,1160,367);
text(s,'7 vật thể · Có 2 cặp chạm nhau · F1 đối tượng = 1,000',60,565,1150,45,28,true,teal);
text(s,'Phân đoạn theo vùng ảnh; không tự gọi tên vật thể như người, xe hay con vật.',60,618,1150,38,22,false,gray);
s=slide('Hình thái học làm sạch và giữ cấu trúc đối tượng',
 '70 giây. Giải thích phần tử cấu trúc B; nền ngoài ảnh bằng 0. Erosion: co. Dilation: giãn. Opening = co rồi giãn; closing = giãn rồi co. Reconstruction giãn marker nhưng bị chặn bởi mask đến hội tụ. Opening by reconstruction khôi phục vùng còn seed. Connected components gán ID các vùng nối nhau theo 4/8 lân cận. Mã tự viết: morpholab/algorithms.py. Nguồn: MorphoLibJ manual v1.6.5, https://imagej.net/plugins/morpholibj ; tài liệu PTIT tại materials/downloads/ptit_morphology.pdf.');
table(s,[['Phép toán','Vai trò trong phân đoạn'],['Erosion / Dilation (co / giãn)','Thu nhỏ hoặc mở rộng vùng theo SE'],['Opening / Closing (mở / đóng)','Loại chi tiết nhỏ hoặc khép khe nhỏ'],['Reconstruction (tái tạo)','Lan từ hạt giống, bị giới hạn bởi mask'],['Connected components (liên thông)','Gán ID cho từng vùng 4 hoặc 8 liên thông']],60,180,1160,320,[525,635]);
text(s,'Tái tạo: X₀ = M;  Xₖ₊₁ = min(δ(Xₖ), F), lặp đến ổn định',60,533,1160,48,27,true,teal);
text(s,'Khối 3×3: diện tích 9 → co còn 1; giãn ảnh gốc thành 25 pixel.',60,600,1160,50,24,false,gray);
s=slide('Khoảng cách tạo địa hình; marker khởi tạo vùng',
 '70 giây. Distance transform: khoảng cách Euclid tới nền. Tâm vùng thường có giá trị lớn. E=-D biến tâm thành đáy vùng. H-maxima dùng reconstruction loại cực đại nông, tránh thừa marker. Watershed lan nhãn bằng heap theo cost(q)=max(cost(p),E(q)). Bản tự cài không tạo dams; xử lý hòa bằng thứ tự vào hàng. Fiji có thể khác ở plateau. EDT dùng bao dưới parabola tuyến tính theo số pixel. Nguồn: algorithms.py; https://cs.brown.edu/people/pfelzens/dt/index.html ; https://imagej.net/plugins/morpholibj.');
text(s,'1. Distance transform (khoảng cách): D(p) = min ‖p − q‖, q thuộc nền\n\n2. H-maxima (lọc cực đại): bỏ đỉnh nông, tạo marker\n\n3. Watershed: lan nhãn trên E = −D, giới hạn trong mask\n\n4. Xuất ảnh nhãn, số lượng, diện tích và tâm từng vùng',60,180,1160,340,28);
text(s,'Hàng đợi ưu tiên: cost(q) = max(cost(p), E(q))',60,554,1160,46,30,true,teal);
text(s,'Quá nhiều marker → chia thừa. Quá ít marker → gộp nhiều vật thể.',60,614,1160,40,24,false,gray);
s=slide('Fiji kiểm chứng theo hai cách khác nhau',
 '70 giây. Shared dùng cùng elevation, markers, mask và liên thông: so sánh bước Watershed. Native chạy Fiji từ ảnh xám: Gaussian, Otsu, hình thái, EDM, extended maxima, Watershed. Native lượng tử 8-bit và SE vuông; Python mặc định float và SE đĩa. Không quy chênh lệch F1 về riêng Watershed. Java adapter gọi JAR thật. Fiji tự tính IoU, Dice và số vùng trong fiji_metrics.csv. Script Groovy chạy lại bằng Script Editor. Nguồn fiji/MorphoBridge.java, NativePipeline.java, ReplayWatershed.groovy và MorphoLibJ manual.');
table(s,[['Kiểm chứng','Đầu vào','Câu hỏi trả lời'],['Fiji shared (chung dữ liệu)','Elevation + marker + mask','Watershed khác nhau thế nào?'],['Fiji native (quy trình riêng)','Ảnh xám chuẩn hóa','Toàn quy trình có chất lượng nào?'],['Ground truth (nhãn đúng)','Nhãn từng vật thể','Có đúng vật thể thật không?']],60,183,1160,300,[310,400,450]);
text(s,'Python và Java/Fiji đều tính định lượng; lưu TIFF, CSV và cấu hình.',60,530,1160,70,28,true,teal);
text(s,'Khác ID màu chưa chắc khác vùng. Cần ghép nhãn trước khi so sánh.',60,610,1160,45,24,false,gray);
s=slide('Dữ liệu và giao thức đánh giá được tách rõ',
 '65 giây. 18 ảnh tổng hợp có GT: 6 validation, 12 test. BBBC039: 200 ảnh nhân tế bào U2OS, chia chính thức 100 training, 50 validation, 50 test. Không train mô hình. Khảo sát 6 validation; bảng chính 50 test × 4 cách =200 dòng. F1 ghép một-một IoU>=0.5, trung bình theo ảnh. IoU/Dice tiền cảnh không đủ nhận diện lỗi chia/gộp. Nguồn https://bbbc.broadinstitute.org/BBBC039 ; manifest, metrics.py, studies.py.');
table(s,[['Nguồn','Quy mô','Mục đích'],['Ảnh tổng hợp','18 ảnh có nhãn','Ví dụ tính đúng và demo'],['BBBC039','200 ảnh; 100 / 50 / 50','Train / validation / test'],['Đối chiếu chính','50 test × 4 cách chạy','200 dòng kết quả, không lỗi'],['Ablation + robustness','6 validation × 7 biến thể / đợt','Từng bước, nhiễu, làm mờ']],60,180,1160,322,[320,360,480]);
text(s,'F1 = 2TP / (2TP + FP + FN) · Ghép một–một với IoU ≥ 0,5',60,535,1160,70,28,true,teal);
text(s,'Bổ sung IoU, Dice, PQ, sai số đếm, chia thừa/gộp sai và thời gian.',60,615,1160,40,24,false,gray);
s=slide('Fiji native có F1 cao hơn trên 50 ảnh test',
 '75 giây. F1 theo ảnh: custom0.7086889, library0.7053689, shared0.7188375, native0.8917349. CI95 bootstrap1000 lần theo ảnh: [.6807,.7305], [.6771,.7277], [.6914,.7386], [.8592,.9132]. Ba cách đầu cùng mask nên IoU tiền cảnh=.8954, native=.8910. Mặt nạ tốt chưa đủ tách đúng từng vật. Khác biệt toàn pipeline, chưa chứng minh một kernel luôn tốt hơn. Nguồn docs/evidence/v2_compare_bbbc039_test/summary.csv và per_image.csv.');
chart(s,['Python tự cài','Python thư viện','Fiji shared','Fiji native'],[.7087,.7054,.7188,.8917],60,176,1160,355);
text(s,'IoU tiền cảnh: 0,8954 ở ba cách đầu; 0,8910 ở Fiji native.',60,552,1160,48,27,true,teal);
text(s,'Tiền xử lý khác nhau. Không suy ra riêng Watershed native vượt trội.',60,609,1160,50,23,false,gray);
s=slide('Khảo sát cho thấy marker cần được kiểm soát',
 '70 giây. Trên 6 validation: baselineF1=.6663, bỏ Gaussian=.6884, rawmarkers=.1563, CCL=.8168. Đây là4/7 biến thể; bảng đầy đủ trong báo cáo. CCL tốt hơn cho thấy baseline còn chia thừa. Blur sigma3 làmF1xuống.6018. Không khẳng định mọi bước hình thái đều cải thiện. Nguồn docs/evidence/v2_ablation_bbbc039/summary.csv và v2_robustness_bbbc039/summary.csv. Các biến đổi cùng ảnh không là mẫu độc lập.');
chart(s,['Baseline hmax','Bỏ Gaussian','Marker chưa lọc','CCL'],[.6663,.6884,.1563,.8168],60,177,1160,345);
text(s,'4 biến thể tiêu biểu trên 6 ảnh validation; bảng đủ 7 biến thể trong báo cáo.',60,535,1160,54,23,false,gray);
text(s,'Làm mờ mạnh (σ = 3): F1 còn 0,6018. Cần xem cả lỗi chia và gộp.',60,605,1160,52,27,true,teal);
s=slide('Kiểm thử tính đúng và đo hiệu năng có kiểm soát',
 '70 giây. Bộ unittest29 trường hợp có kiểm chứng Fiji thật, metric, GUI. Reconstruction5 lần sauwarmup1; mask1,seedtâm, liên thông4; mỗi cặp kết quả bằng nhau. QueuePython chậm hơn synchronousSciPy biên dịch. Đây là so sánh triển khai, không tách riêng độ phức tạp. Không so nativeIOtime trực tiếp với kernelPython. Nguồn docs/evidence/academic_checks/timing_summary.csv, protocol.json ; scripts/academic_checks.py ; tests.');
table(s,[['Ảnh','Queue Python (giây)','Lặp SciPy (giây)'],['48 × 48','0,008983','0,002225'],['96 × 96','0,035766','0,009409'],['160 × 160','0,100107','0,030336']],60,185,1160,265,[330,415,415]);
text(s,'29 kiểm thử · Đầu ra bằng nhau · Trung vị 5 lần, warm-up 1 lần',60,490,1160,76,28,true,teal);
text(s,'Queue chưa nhanh hơn SciPy ở đây. Giữ kết quả bất lợi để đánh giá đúng.',60,590,1160,62,25,false,gray);
s=slide('Đóng góp, giới hạn và cách trình diễn',
 '60 giây. Đóng góp: lý thuyết8 nội dung; tự cài thuật toán; workflowFiji thật; dữ liệu và định lượng; báo cáo và10slide. Demo academic_smoke tạo3casePython vàshared/nativeFiji, mởlabelsCSV. Giới hạn: nền phức tạp, marker nhạy, tốc độPython, không nhận dạng ngữ nghĩa. Có thể cải thiệnmarker và vònglặp, nhưng cần validation độc lập. GUI chỉ hỗ trợ. Nguồn đầy đủ trong báo cáo và https://github.com/jellalaz/XU_LY_ANH.');
text(s,'ĐÃ CÓ',60,185,340,40,25,true,teal);
text(s,'Lý thuyết 8 nội dung; mã tự cài; quy trình Fiji;\nso sánh định lượng; báo cáo và hướng dẫn tái lập.',60,237,1155,92,30);
text(s,'GIỚI HẠN',60,355,340,40,25,true,teal);
text(s,'Nhạy với nền, hình dạng và marker; chưa nhận dạng tên vật thể.\nKết quả tối ưu phải được đo, không suy ra từ ý tưởng.',60,405,1155,94,27);
text(s,'DEMO:  python scripts/academic_smoke.py',60,541,1160,53,30,true,teal);
text(s,'Hướng dẫn: submission/HUONG_DAN_CHAY_VA_TEST.md',60,609,1160,40,23,false,gray);
for(const [i,s] of p.slides.items.entries()){
 const blob=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(`${BUILD}/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await blob.arrayBuffer()));
}
await fs.writeFile(ROOT+'/submission/THUYET_TRINH.md',p.slides.items.map((s,i)=>`## Slide ${i+1}\n\n${s.speakerNotes.text}\n`).join('\n'),'utf8');
const candidatePath=BUILD+'/candidate.pptx';await (await PresentationFile.exportPptx(p)).save(candidatePath);
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath,finalPath:ROOT+'/outputs/presentation_delivery/'+Date.now()+'.pptx',explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[3,5,6,9],requiredNativeChartOwnerSlides:[7,8],materializeLiteralChartWorkbooks:true,pythonExecutable:'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[3,5,6,9].flatMap(n=>['--require-native-table-slide',String(n)])],fontPolicy:{basis:'design',families:['Aptos','Arial']},verifyArtifactToolImport:true,receiptPath:BUILD+'/validation-'+Date.now()+'.json'});
await fs.copyFile(result.finalPath, ROOT+'/submission/PRESENTATION_NHOM_1.pptx'); console.log('Validated presentation: 10 slides, native charts and tables.');
