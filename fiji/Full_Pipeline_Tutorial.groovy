#@ File(label="Anh xam dau vao (synth_00.tif)", style="file") inputFile
#@ File(label="Thu muc MOI de luu ket qua", style="directory") outputFolder
#@ Boolean(label="Hien cac buoc trong Fiji", value=true) showStages
// Standalone Fiji/Groovy pipeline, matching the project's native baseline.
// Fixed protocol: 8-bit min-max, sigma=1, square radius=1, h=2,
// min_area=25, connectivity=4, bright objects, no dams, compactness=0.
import ij.IJ
import ij.ImagePlus
import ij.io.FileSaver
import ij.process.*
import ij.plugin.filter.GaussianBlur
import ij.plugin.filter.EDM
import inra.ijpb.morphology.*
import inra.ijpb.morphology.strel.SquareStrel
import inra.ijpb.binary.BinaryImages
import inra.ijpb.watershed.Watershed

if (!inputFile.isFile()) throw new IllegalArgumentException('Input file does not exist: '+inputFile)
if (!outputFolder.exists() && !outputFolder.mkdirs()) throw new IOException('Cannot create output folder')
if (outputFolder.listFiles().length > 0) throw new IllegalArgumentException('Choose an EMPTY output folder')
def image=IJ.openImage(inputFile.absolutePath)
if (image==null || image.stackSize!=1 || image.bitDepth==24)
    throw new IllegalArgumentException('Use a single 2D grayscale image (8/16/32-bit)')
int w=image.width, ht=image.height, conn=4, minArea=25
double sigma=1, h=2
def raw=image.getProcessor()
double lo=Double.POSITIVE_INFINITY, hi=Double.NEGATIVE_INFINITY
for (int y=0;y<ht;y++) for (int x=0;x<w;x++) {
    double v=raw.getf(x,y)
    if (!Double.isFinite(v)) throw new IllegalArgumentException('Non-finite input pixel')
    lo=Math.min(lo,v);hi=Math.max(hi,v)
}
def gray=new FloatProcessor(w,ht)
for (int y=0;y<ht;y++) for (int x=0;x<w;x++) gray.setf(x,y,(float)(hi>lo?(raw.getf(x,y)-lo)/(hi-lo):0))
def save={String name,ImageProcessor processor ->
    def imp=new ImagePlus(name,processor.duplicate())
    imp.resetDisplayRange()
    if (!new FileSaver(imp).saveAsTiff(new File(outputFolder,name+'.tif').absolutePath)) throw new IOException('Save failed: '+name)
    if (showStages) {
        if (name in ['native_markers','morpholibj_labels']) {
            IJ.run(imp,'3-3-2 RGB','') // LUT only: keep label pixel IDs unchanged.
        }
        imp.show()
    }
}
save('gray',gray)
gray.setMinAndMax(0,1)
def smooth=(ByteProcessor)gray.convertToByte(true)
save('input_8bit',smooth)
new GaussianBlur().blurGaussian(smooth,sigma,sigma,0.01)
save('smoothed_8bit',smooth)
int threshold=new AutoThresholder().getThreshold(AutoThresholder.Method.Otsu,smooth.histogram)
def binary=new ByteProcessor(w,ht)
for (int y=0;y<ht;y++) for (int x=0;x<w;x++) binary.set(x,y,smooth.get(x,y)>threshold?255:0)
save('native_binary',binary)
def se=SquareStrel.fromRadius(1)
def eroded=Morphology.erosion(binary,se)
save('native_erosion',eroded)
save('native_dilation',Morphology.dilation(binary,se))
save('native_opening',Morphology.opening(binary,se))
save('native_closing',Morphology.closing(binary,se))
def mask=Reconstruction.reconstructByDilation(eroded,binary,conn)
save('native_reconstruction',mask)
mask=Reconstruction.fillHoles(mask)
def components=BinaryImages.componentsLabeling(mask,conn,32)
def areas=[:]
for (int y=0;y<ht;y++) for (int x=0;x<w;x++) {
    int id=(int)components.getf(x,y)
    if (id>0) areas[id]=(areas[id]?:0)+1
}
for (int y=0;y<ht;y++) for (int x=0;x<w;x++)
    if ((areas[(int)components.getf(x,y)]?:0)<minArea) mask.setf(x,y,0)
components=BinaryImages.componentsLabeling(mask,conn,32)
save('native_mask',mask);save('native_components',components)
def distance=new EDM().makeFloatEDM(mask,0,true)
save('native_distance',distance)
def peaks=MinimaAndMaxima.extendedMaxima(distance,h,conn)
for (int y=0;y<ht;y++) for (int x=0;x<w;x++) if (mask.getf(x,y)==0) peaks.setf(x,y,0)
save('native_maxima',peaks)
def markers=BinaryImages.componentsLabeling(peaks,conn,32)
def seeded=[] as Set
def best=[:]
int nextId=0
for (int y=0;y<ht;y++) for (int x=0;x<w;x++) {
    int id=(int)components.getf(x,y),m=(int)markers.getf(x,y)
    nextId=Math.max(nextId,m)
    if(m>0) seeded.add(id)
    if(id>0 && (!best.containsKey(id) || distance.getf(x,y)>distance.getf(best[id][0],best[id][1]))) best[id]=[x,y]
}
best.keySet().each { id -> if(!seeded.contains(id)){ def xy=best[id];markers.setf(xy[0],xy[1],++nextId) } }
save('native_markers',markers)
def elevation=(FloatProcessor)distance.duplicate();elevation.multiply(-1)
save('native_elevation',elevation)
def labels=Watershed.computeWatershed(new ImagePlus('elevation',elevation),new ImagePlus('markers',markers),new ImagePlus('mask',mask),conn,false,false)
if(labels==null) throw new IllegalStateException('Watershed failed; inspect mask/markers')
save('morpholibj_labels',labels.getProcessor())
def ids=[] as Set
for(int y=0;y<ht;y++) for(int x=0;x<w;x++) if(labels.getProcessor().getf(x,y)>0) ids.add((int)labels.getProcessor().getf(x,y))
String csv='predicted_objects,foreground_iou,foreground_dice,true_objects\n'
String stem=inputFile.name.replaceFirst(/\.[^.]+$/,'')
def gtFile=new File(inputFile.parentFile,stem+'_gt.tif')
if(gtFile.isFile()) {
    def gt=IJ.openImage(gtFile.absolutePath)
    if(gt.width!=w || gt.height!=ht) throw new IllegalArgumentException('Ground truth size mismatch')
    def trueIds=[] as Set
    long intersection=0,union=0,total=0
    for(int y=0;y<ht;y++) for(int x=0;x<w;x++) {
        int id=(int)gt.getProcessor().getf(x,y)
        boolean a=id>0,b=labels.getProcessor().getf(x,y)>0
        if(a) trueIds.add(id)
        if(a && b) intersection++
        if(a || b) union++
        if(a) total++
        if(b) total++
    }
    csv+=ids.size()+','+(union==0?1.0:(double)intersection/union)+','+(total==0?1.0:2.0*intersection/total)+','+trueIds.size()+'\n'
} else csv+=ids.size()+',,,\n'
new File(outputFolder,'fiji_metrics.csv').setText(csv,'UTF-8')
new File(outputFolder,'parameters.txt').setText('Source='+inputFile.absolutePath+'\nRaw min='+lo+'; max='+hi+'\n8-bit min-max; Gaussian sigma=1; accuracy=0.01; ImageJ Otsu threshold='+threshold+'\nSquare SE radius=1; reconstruction connectivity=4; fill holes plugin default\nmin_area=25; ImageJ float EDM background=0, edgesAreBackground=true\nh=2; connectivity=4; no dams; compactness=0\nGround truth used only AFTER segmentation for metrics: '+gtFile.absolutePath+'\n','UTF-8')
IJ.log('Full Fiji pipeline completed: '+ids.size()+' objects; output='+outputFolder.absolutePath)
