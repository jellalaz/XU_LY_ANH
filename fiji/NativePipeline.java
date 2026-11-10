import ij.IJ;
import ij.ImagePlus;
import ij.io.FileSaver;
import ij.process.*;
import ij.plugin.filter.GaussianBlur;
import ij.plugin.filter.EDM;
import inra.ijpb.morphology.*;
import inra.ijpb.morphology.strel.SquareStrel;
import inra.ijpb.binary.BinaryImages;
import inra.ijpb.watershed.Watershed;
import java.nio.file.*;
import java.util.*;

/** Quy trình Fiji độc lập từ ảnh xám; khác phép kiểm chứng chung ba đầu vào. */
public class NativePipeline {
    public static void save(Path dir,String name,ImageProcessor p) {
        if(!new FileSaver(new ImagePlus(name,p)).saveAsTiff(dir.resolve(name+".tif").toString()))
            throw new IllegalStateException("Cannot save "+name);
    }
    public static void main(String[] args) {
        try { execute(args); System.exit(0); }
        catch(Throwable error) { error.printStackTrace(); System.exit(1); }
    }
    public static void execute(String[] args) throws Exception {
        System.setProperty("java.awt.headless","true");
        Path dir=Paths.get(args[0]); int radius=Integer.parseInt(args[1]);
        double h=Double.parseDouble(args[2]); int conn=Integer.parseInt(args[3]);
        double sigma=Double.parseDouble(args[4]); int minArea=Integer.parseInt(args[5]);
        boolean bright=Boolean.parseBoolean(args[6]);
        ImageProcessor input=IJ.openImage(dir.resolve("gray.tif").toString()).getProcessor();
        long start=System.nanoTime();
        input.setMinAndMax(0,1); ByteProcessor smooth=(ByteProcessor)input.convertToByte(true);
        if(sigma>0) new GaussianBlur().blurGaussian(smooth,sigma,sigma,.01);
        int threshold=new AutoThresholder().getThreshold(AutoThresholder.Method.Otsu,smooth.getHistogram());
        ByteProcessor binary=new ByteProcessor(input.getWidth(),input.getHeight());
        for(int y=0;y<binary.getHeight();y++) for(int x=0;x<binary.getWidth();x++) {
            boolean fg=bright?smooth.get(x,y)>threshold:smooth.get(x,y)<threshold;
            binary.set(x,y,fg?255:0);
        }
        save(dir,"native_binary",binary);
        Strel se=SquareStrel.fromRadius(radius);
        ImageProcessor erosion=Morphology.erosion(binary,se);
        save(dir,"native_erosion",erosion);
        save(dir,"native_dilation",Morphology.dilation(binary,se));
        save(dir,"native_opening",Morphology.opening(binary,se));
        save(dir,"native_closing",Morphology.closing(binary,se));
        ImageProcessor mask=Reconstruction.reconstructByDilation(erosion,binary,conn);
        save(dir,"native_reconstruction",mask);
        mask=Reconstruction.fillHoles(mask);
        ImageProcessor components=BinaryImages.componentsLabeling(mask,conn,32);
        Map<Integer,Integer> areas=new HashMap<>();
        for(int y=0;y<mask.getHeight();y++) for(int x=0;x<mask.getWidth();x++) {
            int id=(int)components.getf(x,y); if(id>0) areas.put(id,areas.getOrDefault(id,0)+1);
        }
        for(int y=0;y<mask.getHeight();y++) for(int x=0;x<mask.getWidth();x++)
            if(areas.getOrDefault((int)components.getf(x,y),0)<minArea) mask.setf(x,y,0);
        components=BinaryImages.componentsLabeling(mask,conn,32);
        save(dir,"native_mask",mask); save(dir,"native_components",components);
        FloatProcessor distance=new EDM().makeFloatEDM(mask,0,true);
        save(dir,"native_distance",distance);
        ImageProcessor peaks=MinimaAndMaxima.extendedMaxima(distance,h,conn);
        for(int y=0;y<mask.getHeight();y++) for(int x=0;x<mask.getWidth();x++) if(mask.getf(x,y)==0) peaks.setf(x,y,0);
        ImageProcessor markers=BinaryImages.componentsLabeling(peaks,conn,32);
        Set<Integer> seeded=new HashSet<>(); Map<Integer,int[]> best=new HashMap<>();
        int next=0;
        for(int y=0;y<mask.getHeight();y++) for(int x=0;x<mask.getWidth();x++) {
            int id=(int)components.getf(x,y), m=(int)markers.getf(x,y); next=Math.max(next,m);
            if(m>0) seeded.add(id);
            if(id>0 && (!best.containsKey(id) || distance.getf(x,y)>distance.getf(best.get(id)[0],best.get(id)[1]))) best.put(id,new int[]{x,y});
        }
        for(int id:best.keySet()) if(!seeded.contains(id)) {int[] xy=best.get(id); markers.setf(xy[0],xy[1],++next);}
        save(dir,"native_markers",markers);
        FloatProcessor elevation=(FloatProcessor)distance.duplicate(); elevation.multiply(-1);
        save(dir,"native_elevation",elevation);
        ImagePlus result=Watershed.computeWatershed(new ImagePlus("elevation",elevation),new ImagePlus("markers",markers),new ImagePlus("mask",mask),conn,false,false);
        double seconds=(System.nanoTime()-start)/1e9;
        MorphoBridge.saveResult(dir,result,seconds,"pipeline_seconds_including_intermediate_io");
        Files.writeString(dir.resolve("native_parameters.txt"),"Independent Fiji pipeline\n8-bit quantization; ImageJ Otsu; Gaussian sigma="+sigma+"; threshold="+threshold+"\nSquare SE radius="+radius+"; opening by reconstruction; fill holes using plugin default\nImageJ EDM; MorphoLibJ extended maxima h="+h+"; connectivity="+conn+"; min area="+minArea+"\nNative pipeline seconds (includes intermediate TIFF writes)="+seconds+"\n");
    }
}
