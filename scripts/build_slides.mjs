// Dựng lại 10 slide theo bố cục cũ, kèm lời trình bày tổng cộng 15 phút.
// Chỉ dùng hình dữ liệu thật và ảnh chụp Fiji, bảng/biểu đồ vẫn sửa được.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..').replaceAll('\\','/');
const NODE_MODULES=process.env.CODEX_NODE_MODULES || 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const SKILL=process.env.CODEX_PRESENTATIONS_SKILL || 'C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1104.22356/skills/presentations';
process.env.RUNTIME_NODE_MODULES ||= NODE_MODULES;
const PYTHON=process.env.CODEX_RUNTIME_PYTHON || 'C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const {FileBlob,Presentation,PresentationFile}=await import(pathToFileURL(NODE_MODULES+'/@oai/artifact-tool/dist/artifact_tool.mjs'));
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs'));
const BUILD=ROOT+'/outputs/presentation_build';
await fs.mkdir(BUILD,{recursive:true});
await fs.mkdir(ROOT+'/outputs/presentation_delivery',{recursive:true});
const existing=ROOT+'/submission/PRESENTATION_NHOM_1.pptx';
try {
 const source=await PresentationFile.importPptx(await FileBlob.load(existing));
 const inspect=await source.inspect({kind:'slide,textbox,table,chart',maxChars:20000});
 await fs.writeFile(BUILD+'/source-inspection.json',JSON.stringify(inspect,null,2));
} catch(error) {throw new Error('Cannot inspect source deck: '+error.message);}
const p=Presentation.create({slideSize:{width:1280,height:720}});
const navy='#102D43',teal='#087F8C',gray='#435466';
const times=[45,100,100,110,100,100,95,100,100,50];
const noteSections=(await fs.readFile(ROOT+'/submission/THUYET_TRINH.md','utf8')).split(/^## Slide [^\n]+\n/gm).slice(1);
if(noteSections.length!==10)throw new Error('Need 10 speaker-note sections');
function text(s,value,x,y,w,h,size=26,bold=false,color=navy){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=value;q.text.style={fontFamily:'Arial',fontSize:size,bold,color};return q;
}
function slide(title){const s=p.slides.add();s.background.fill='#FFFFFF';
 text(s,'PTIT / NHÓM 1 / XỬ LÝ ẢNH',58,26,1100,26,15,true,teal);
 text(s,title,58,76,1160,100,38,true);
 text(s,'Hình thái học và Watershed',58,675,1050,22,14,false,gray);
 text(s,String(p.slides.items.length).padStart(2,'0'),1170,670,52,28,18,true,teal);
 const seconds=times[p.slides.items.length-1];
 s.speakerNotes.text=noteSections[p.slides.items.length-1].trim();
 return s;
}
function table(s,values,x,y,w,h,widths,size=24){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let cell=t.getCell(r,c);cell.fill=r===0?'#E9F1F5':r%2?'#F6F8FA':'#FFFFFF';cell.text.style={fontFamily:'Arial',fontSize:size,bold:r===0,color:navy};}
 t.borders.assign({style:'solid',fill:'#CED9E0',width:1});return t;
}
async function picture(s,file,x,y,w,h){const b=await fs.readFile(ROOT+'/'+file);s.images.add({blob:new Uint8Array(b).buffer,contentType:'image/png',alt:'Dữ liệu và ảnh chụp thực hành của nhóm',fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function chart(s,categories,values,x,y,w,h,size=22){const c=s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories,series:[{name:'F1 đối tượng',values,fill:teal}],hasLegend:false,dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0000',textStyle:{fontSize:size}},xAxis:{textStyle:{fontSize:size}},yAxis:{min:0,max:1,textStyle:{fontSize:18},majorGridlines:{fill:'#DDE4E9',width:1,style:'solid'}}});applyPresentationChartFont(c,{fontFamily:'Arial'});return c;}
let s=slide('Phân đoạn đối tượng bằng\nhình thái học toán học và Watershed');
text(s,'Python tự cài và Fiji / MorphoLibJ 1.6.5',60,230,1150,52,30,true,teal);
text(s,'Thực hành từ ảnh gốc, kiểm chứng bằng nhãn đúng',60,313,1150,60,29);
text(s,'Kiều Trường Giang — B23DCCN254\nTrần Đỗ Lan Phương — B23DCCN667\nGiang Thùy Tiên — B23DCCN814\nPhạm Văn Vỹ — B23DCCN954',60,454,1100,148,23,false,gray);

s=slide('Các toán tử hình thái và phần tử cấu trúc');
await picture(s,'submission/latex/figures/morphology.png',60,173,790,440);
text(s,'Co: MIN\nGiãn: MAX\n\nMở: co rồi giãn\nĐóng: giãn rồi co',885,198,330,230,27,true);
text(s,'Tái tạo: lan seed\ntrong mask tới ổn định',885,469,330,96,25,false,teal);
text(s,'Cùng Square r = 1; ảnh trung gian do Fiji tính thật.',60,625,1150,32,23,false,gray);

s=slide('Fiji: từ ảnh gốc đến mặt nạ sạch');
await picture(s,'submission/latex/figures/manual_preprocess.png',60,187,1160,315);
text(s,'Tái tạo, lấp lỗ kín, loại vùng nhỏ hơn 25 pixel',60,526,1160,48,28,true,teal);
text(s,'Mask có 5 khối liên thông. Hai cặp vật vẫn đang dính.',60,595,1160,48,27);

s=slide('Fiji: distance, marker và Watershed');
await picture(s,'submission/latex/figures/manual_watershed.png',60,166,1160,436);
text(s,'5 vùng liên thông thành 7 nhãn. Marker có ID, mask giới hạn miền lan.',60,616,1160,41,25,true,teal);

s=slide('Đo trong Fiji và chấm lại bằng Python');
await picture(s,'submission/latex/figures/ui_overlap.png',60,185,540,390);
table(s,[['Chỉ số','Kết quả làm tay'],['IoU tiền cảnh','0,980451'],['Dice tiền cảnh','0,990129'],['Đối tượng / F1','7 / 1,0000']],650,204,570,300,[295,275],25);
text(s,'IoU/Dice đo vật–nền; F1 đánh giá từng đối tượng sau ghép nhãn.',60,604,1160,51,25,true,teal);

s=slide('Code Python và hai cách kiểm chứng Fiji');
text(s,'algorithms.py: toán tử tự cài\npipeline.py: ghép quy trình\nmetrics.py: đánh giá nhãn đúng',60,186,1160,150,30,true);
table(s,[['Đối chiếu','Giữ chung / thay đổi'],['Fiji shared','Cùng elevation, marker, mask; so bước Watershed'],['Fiji native','Tự xử lý ảnh xám; so toàn pipeline']],60,374,1160,180,[305,855],24);
text(s,'Watershed tự cài: cost(q) = max(cost(p), E(q))',60,603,1160,48,28,true,teal);

s=slide('Dữ liệu thật và giao thức đánh giá');
await picture(s,'submission/latex/figures/real_example.png',60,173,680,440);
text(s,'200 ảnh thật có nhãn\n100 / 50 / 50\n\n50 ảnh test, 5.720 vật\n4 cách chạy, 200 dòng',780,196,435,255,28,true);
text(s,'Khảo sát thêm: 6 validation\nKhông huấn luyện mô hình',780,492,435,100,24,false,teal);

s=slide('Kết quả đối chiếu trên 50 ảnh test');
chart(s,['Python tự cài','Python thư viện','Fiji shared','Fiji native'],[.7087,.7054,.7188,.8917],60,178,1160,364);
text(s,'IoU tiền cảnh: 0,8954 ở ba cách đầu; Fiji native: 0,8910.',60,557,1160,46,26,true,teal);
text(s,'Khác biệt toàn pipeline. Chưa chứng minh riêng một hàm Watershed tốt hơn.',60,615,1160,40,23,false,gray);

s=slide('Khảo sát marker và đo hiệu năng');
chart(s,['Marker raw','H-maxima','CCL'],[.1563,.6663,.8168],60,194,650,330,21);
table(s,[['Reconstruction','160 × 160'],['Queue Python','0,100107 s'],['Lặp SciPy','0,030336 s']],770,225,450,235,[240,210],23);
text(s,'6 ảnh validation; chưa đủ để kết luận tổng quát.',60,548,1160,44,25,true,teal);
text(s,'Thử tối ưu phải đo. Queue Python chưa nhanh hơn trong benchmark này.',60,612,1160,43,24,false,gray);

s=slide('Phần mở rộng MorphoLab và kết luận');
await picture(s,'submission/latex/figures/morpholab_app.png',60,180,745,405);
text(s,'Dùng chung code nghiên cứu\n\nChọn ảnh, xem các bước\nChỉnh tham số, lưu kết quả',840,211,375,248,26,true);
text(s,'Hạn chế: nhạy nền và marker\nMở rộng khảo sát validation',840,490,375,95,23,false,teal);
text(s,'Bằng chứng chính: mã nguồn, TIFF nhãn, CSV và báo cáo tái lập.',60,617,1160,40,24,false,gray);

if(times.reduce((a,b)=>a+b,0)!==900 || p.slides.items.length!==10)throw new Error('Timing or slide-count mismatch');
for(const [i,s] of p.slides.items.entries()){
 const blob=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(`${BUILD}/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await blob.arrayBuffer()));
}
const candidatePath=BUILD+'/candidate.pptx';await(await PresentationFile.exportPptx(p)).save(candidatePath);
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath,finalPath:ROOT+'/outputs/presentation_delivery/'+Date.now()+'.pptx',explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[5,6,9],requiredNativeChartOwnerSlides:[8,9],materializeLiteralChartWorkbooks:true,pythonExecutable:PYTHON,integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[5,6,9].flatMap(n=>['--require-native-table-slide',String(n)])],fontPolicy:{basis:'design',families:['Arial','Aptos']},verifyArtifactToolImport:true,receiptPath:BUILD+'/validation-'+Date.now()+'.json'});
await fs.copyFile(result.finalPath,ROOT+'/submission/PRESENTATION_NHOM_1.pptx');
await fs.writeFile(BUILD+'/timing.json',JSON.stringify({slides:10,seconds:times,total_seconds:900},null,2));
console.log('PASS: 10 slides, 900 seconds, editable charts/tables.');
