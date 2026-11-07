import ij.IJ;
import ij.ImagePlus;
import ij.io.FileSaver;
import ij.process.ImageProcessor;
import inra.ijpb.watershed.Watershed;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Actual MorphoLibJ reference; no Python watershed inside this bridge. */
public class MorphoBridge {
    public static void main(String[] args) {
        try { execute(args); System.exit(0); }
        catch(Throwable error) { error.printStackTrace(); System.exit(1); }
    }
    public static void execute(String[] args) throws Exception {
        System.setProperty("java.awt.headless", "true");
        Path dir=Paths.get(args[0]);
        int connectivity=Integer.parseInt(args[1]);
        if(connectivity!=4 && connectivity!=8) throw new IllegalArgumentException("Connectivity 4/8 required");
        ImagePlus elevation=IJ.openImage(dir.resolve("elevation.tif").toString());
        ImagePlus markers=IJ.openImage(dir.resolve("markers.tif").toString());
        ImagePlus mask=IJ.openImage(dir.resolve("mask.tif").toString());
        if(elevation==null || markers==null || mask==null) throw new IllegalArgumentException("Missing bridge inputs");
        long start=System.nanoTime();
        ImagePlus result=Watershed.computeWatershed(elevation,markers,mask,connectivity,false,false);
        double seconds=(System.nanoTime()-start)/1e9;
        saveResult(dir,result,seconds);
    }

    public static void saveResult(Path dir,ImagePlus result,double seconds) throws Exception {
        saveResult(dir,result,seconds,"watershed_seconds");
    }

    public static void saveResult(Path dir,ImagePlus result,double seconds,String timingName) throws Exception {
        if(result==null || !new FileSaver(result).saveAsTiff(dir.resolve("morpholibj_labels.tif").toString()))
            throw new IllegalStateException("MorphoLibJ returned no result");
        Set<Integer> objects=new HashSet<>();
        ImageProcessor pred=result.getProcessor();
        for(int y=0;y<pred.getHeight();y++) for(int x=0;x<pred.getWidth();x++) {
            int value=(int)pred.getf(x,y); if(value>0) objects.add(value);
        }
        String csv=timingName+",predicted_objects,foreground_iou,foreground_dice,true_objects\n";
        Path gtPath=dir.resolve("ground_truth.tif");
        if(Files.exists(gtPath)) {
            ImageProcessor gt=IJ.openImage(gtPath.toString()).getProcessor();
            if(gt.getWidth()!=pred.getWidth() || gt.getHeight()!=pred.getHeight()) throw new IllegalArgumentException("GT shape mismatch");
            Set<Integer> gtObjects=new HashSet<>();
            long intersection=0,union=0,total=0;
            for(int y=0;y<gt.getHeight();y++) for(int x=0;x<gt.getWidth();x++) {
                int g=(int)gt.getf(x,y); boolean a=g>0,b=pred.getf(x,y)>0;
                if(g>0) gtObjects.add(g);
                if(a && b) intersection++; if(a || b) union++;
                if(a) total++; if(b) total++;
            }
            csv+=seconds+","+objects.size()+","+(union==0?1.:(double)intersection/union)+","+(total==0?1.:2.*intersection/total)+","+gtObjects.size()+"\n";
        } else csv+=seconds+","+objects.size()+",,,\n";
        Files.writeString(dir.resolve("fiji_metrics.csv"),csv,StandardCharsets.UTF_8);
        System.out.println("MorphoLibJ reference completed: "+objects.size()+" objects, "+seconds+" s");
    }
}
