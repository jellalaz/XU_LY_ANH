#@ File(label="Thu muc ket qua Fiji chua elevation markers mask", style="directory") folder
#@ Integer(label="Lien thong (4 hoac 8)", value=4) connectivity
#@ Boolean(label="Hien anh ket qua", value=true) showImages
import ij.IJ
import inra.ijpb.watershed.Watershed
def dir = folder.getAbsolutePath()
if (!(connectivity in [4, 8])) throw new IllegalArgumentException("Connectivity must be 4 or 8")
def images = ["elevation", "markers", "mask"].collect { name ->
    def file = new File(folder, name + ".tif")
    if (!file.isFile()) throw new IllegalArgumentException("Missing " + file)
    IJ.openImage(file.getAbsolutePath())
}
if (showImages) images.each { it.show() }
def labels = Watershed.computeWatershed(images[0], images[1], images[2], connectivity, false, false)
labels.setTitle("MorphoLibJ labels nhom 1")
if (showImages) labels.show()
IJ.saveAsTiff(labels, new File(folder, "fiji_interactive_labels.tif").getAbsolutePath())
IJ.log("Saved Fiji labels, connectivity=" + connectivity + ", no dams: " + dir)
