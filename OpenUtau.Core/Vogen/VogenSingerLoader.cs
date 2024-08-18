using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Newtonsoft.Json;
using OpenUtau.Core.Ustx;
using OpenUtau.Core.Util;
using Serilog;
using SharpCompress.Archives;
using SharpCompress.Common;

namespace OpenUtau.Core.Vogen {
    [Serializable]
    public class VogenMeta {  // Change this to public if it's used elsewhere
        public string name;
        public string id;
        public string version;
        public string builtBy;
        public string voiceBy;
        public string avatar;
        public string portrait;
        public float portraitOpacity = 0.67f;
        public int portraitHeight = 0;
        public string web;
        public string misc;
    }

    public class VogenSingerLoader {
        readonly string basePath;

        public static IEnumerable<USinger> FindAllSingers() {
            List<USinger> singers = new List<USinger>();
            foreach (var path in PathManager.Inst.SingersPaths) {
                var loader = new VogenSingerLoader(path);
                singers.AddRange(loader.SearchAll());
            }
            return singers;
        }

        public VogenSingerLoader(string basePath) {
            this.basePath = basePath;
        }

        public IEnumerable<USinger> SearchAll() {
            var result = new List<USinger>();
            if (!Directory.Exists(basePath)) {
                Log.Warning($"Directory does not exist: {basePath}");
                Console.WriteLine($"Directory does not exist: {basePath}");
                return result;
            }

            IEnumerable<string> files;
            if (Preferences.Default.LoadDeepFolderSinger) {
                files = Directory.EnumerateFiles(basePath, "*.vogeon", SearchOption.AllDirectories);
            } else {
                files = Directory.EnumerateFiles(basePath, "*.vogeon");
            }

            result.AddRange(files.Select(filePath => {
                try {
                    return LoadSinger(filePath);
                } catch (Exception e) {
                    Log.Error(e, $"Failed to load Vogen singer from: {filePath}");
                    Console.WriteLine($"Failed to load Vogen singer from: {filePath}, Error: {e.Message}");
                    return null;
                }
            }).OfType<USinger>());

            return result;
        }

        public USinger LoadSinger(string filePath) {
            Console.WriteLine($"Attempting to load singer from: {filePath}");
            Log.Information($"Attempting to load singer from: {filePath}");

            VogenMeta meta;
            byte[] model;
            byte[] avatar = null;

            try {
                using (var archive = ArchiveFactory.Open(filePath)) {
                    var metaEntry = archive.Entries.FirstOrDefault(e => e.Key == "meta.json");
                    if (metaEntry == null) {
                        throw new ArgumentException("Missing meta.json");
                    }

                    using (var stream = metaEntry.OpenEntryStream()) {
                        using var reader = new StreamReader(stream, Encoding.UTF8);
                        JsonSerializer serializer = new JsonSerializer();
                        meta = (VogenMeta)serializer.Deserialize(reader, typeof(VogenMeta));
                    }

                    model = Zip.ExtractBytes(archive, "model.onnx");
                    if (model == null) {
                        throw new ArgumentException("Missing model.onnx");
                    }

                    if (!string.IsNullOrEmpty(meta.avatar)) {
                        avatar = Zip.ExtractBytes(archive, meta.avatar);
                    }
                }
            } catch (Exception ex) {
                Log.Error(ex, $"Failed to load singer from: {filePath}");
                Console.WriteLine($"Failed to load singer from: {filePath}, Error: {ex.Message}");
                throw; // Rethrow the exception after logging it
            }

            Console.WriteLine($"Singer loaded successfully from: {filePath}");
            Log.Information($"Singer loaded successfully from: {filePath}");
            return new VogenSinger(filePath, meta, model, avatar);
        }
    }
}
