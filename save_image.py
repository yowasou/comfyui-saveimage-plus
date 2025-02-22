from comfy.cli_args import args
import folder_paths
import json
import numpy
import os
from PIL import Image, ExifTags
from PIL.PngImagePlugin import PngInfo

class SaveImagePlus:
    def __init__(self):
        pass

    FILE_TYPE_PNG = "PNG"
    FILE_TYPE_JPEG = "JPEG"
    FILE_TYPE_WEBP_LOSSLESS = "WEBP (lossless)"
    FILE_TYPE_WEBP_LOSSY = "WEBP (lossy)"
    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "file_type": ([s.FILE_TYPE_PNG, s.FILE_TYPE_JPEG, s.FILE_TYPE_WEBP_LOSSLESS, s.FILE_TYPE_WEBP_LOSSY], ),
                "remove_metadata": ("BOOLEAN", {"default": False}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    def save_images(self, images, filename_prefix="ComfyUI", file_type=FILE_TYPE_PNG, remove_metadata=False, prompt=None, extra_pnginfo=None):
        output_dir = folder_paths.get_output_directory()
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
        extension = {
            self.FILE_TYPE_PNG: "png",
            self.FILE_TYPE_JPEG: "jpg",
            self.FILE_TYPE_WEBP_LOSSLESS: "webp",
            self.FILE_TYPE_WEBP_LOSSY: "webp",
        }.get(file_type, "png")

        results = []
        for image in images:
            array = 255. * image.cpu().numpy()
            img = Image.fromarray(numpy.clip(array, 0, 255).astype(numpy.uint8))

            kwargs = dict()
            if extension == "png":
                kwargs["compress_level"] = 4
                if not remove_metadata and not args.disable_metadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                    kwargs["pnginfo"] = metadata
            else:
                if file_type == self.FILE_TYPE_WEBP_LOSSLESS:
                    kwargs["lossless"] = True
                else:
                    kwargs["quality"] = 90
                if not remove_metadata and not args.disable_metadata:
                    metadata = {}
                    if prompt is not None:
                        metadata["prompt"] = prompt
                    if extra_pnginfo is not None:
                        metadata.update(extra_pnginfo)
                    exif = img.getexif()
                    exif[ExifTags.Base.UserComment] = json.dumps(metadata)
                    kwargs["exif"] = exif.tobytes()
                    # JSON を辞書に変換
                    data = json.loads(exif[ExifTags.Base.UserComment])
                    # "masterpiece" を含む属性を抽出
                    positive = next(find_masterpiece_strings(data), None)
                    kwargs["exif"] = positive.encode("utf-8", errors="ignore")
                    exkwargs = kwargs

            file = f"{filename}_{counter:05}_.{extension}"
            img.save(os.path.join(full_output_folder, file), **kwargs)
            # add exfile
            exfile = f"{filename}_exfile{counter:05}_.{extension}"
            img.save(os.path.join(full_output_folder, exfile), **exkwargs)

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": "output",
            })
            counter += 1

        return { "ui": { "images": results, "positive": positive} }

def find_masterpiece_strings(data):
    #再帰的に 'masterpiece' を含む文字列を探すジェネレータ
    if isinstance(data, dict):
        for v in data.values():
            yield from find_masterpiece_strings(v)
    elif isinstance(data, list):
        for item in data:
            yield from find_masterpiece_strings(item)
    elif isinstance(data, str) and "masterpiece" in data:
        yield data
    
NODE_CLASS_MAPPINGS = {
    "SaveImagePlus": SaveImagePlus
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImagePlus": "Save Image Plus"
}

WEB_DIRECTORY = "web"
