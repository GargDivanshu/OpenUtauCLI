using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using OpenUtau.Api;
using OpenUtau.Classic;
using OpenUtau.Core.Lib;
using OpenUtau.Core.Ustx;
using OpenUtau.Core.Util;
using Serilog;

namespace OpenUtau.Core {
    public struct ValidateOptions {
        public bool SkipTiming;
        public UPart Part;
        public bool SkipPhonemizer;
        public bool SkipPhoneme;
    }

    public class DocManager : SingletonBase<DocManager> {
        DocManager() {
            Project = new UProject();
            Console.WriteLine("DocManager initialized with a new UProject.");
        }

        private Thread mainThread;
        private TaskScheduler mainScheduler;

        public int playPosTick = 0;

        public TaskScheduler MainScheduler => mainScheduler;
        public Action<Action> PostOnUIThread { get; set; }
        public Plugin[] Plugins { get; private set; }
        public PhonemizerFactory[] PhonemizerFactories { get; private set; }
        public UProject Project { get; private set; }
        public bool HasOpenUndoGroup => undoGroup != null;
        public List<UPart> PartsClipboard { get; set; }
        public List<UNote> NotesClipboard { get; set; }
        internal PhonemizerRunner PhonemizerRunner { get; private set; }

        public void Initialize() {
            AppDomain.CurrentDomain.UnhandledException += new UnhandledExceptionEventHandler((sender, args) => {
                CrashSave();
            });
            SearchAllPlugins();
            SearchAllLegacyPlugins();
            mainThread = Thread.CurrentThread;
            // mainScheduler = TaskScheduler.FromCurrentSynchronizationContext();
            mainScheduler = TaskScheduler.Current;
            PhonemizerRunner = new PhonemizerRunner(mainScheduler);
            Console.WriteLine("DocManager initialized.");
        }

        public void SearchAllLegacyPlugins() {
            try {
                var stopWatch = Stopwatch.StartNew();
                Plugins = PluginLoader.LoadAll(PathManager.Inst.PluginsPath);
                stopWatch.Stop();
                Console.WriteLine($"Search all legacy plugins completed in: {stopWatch.Elapsed}");
                Log.Information($"Search all legacy plugins: {stopWatch.Elapsed}");
            } catch (Exception e) {
                Console.WriteLine("Failed to search legacy plugins.");
                Log.Error(e, "Failed to search legacy plugins.");
                Plugins = new Plugin[0];
            }
        }

        public void SearchAllPlugins() {
            const string kBuiltin = "OpenUtau.Plugin.Builtin.dll";
            var stopWatch = Stopwatch.StartNew();
            var phonemizerFactories = new List<PhonemizerFactory>();
            var files = new List<string>();
            try {
                files.Add(Path.Combine(Path.GetDirectoryName(AppContext.BaseDirectory), kBuiltin));
                Directory.CreateDirectory(PathManager.Inst.PluginsPath);
                string oldBuiltin = Path.Combine(PathManager.Inst.PluginsPath, kBuiltin);
                if (File.Exists(oldBuiltin)) {
                    File.Delete(oldBuiltin);
                }
                files.AddRange(Directory.EnumerateFiles(PathManager.Inst.PluginsPath, "*.dll", SearchOption.AllDirectories));
            } catch (Exception e) {
                Console.WriteLine("Failed to search plugins.");
                Log.Error(e, "Failed to search plugins.");
            }
            foreach (var file in files) {
                Assembly assembly;
                try {
                    if (!LibraryLoader.IsManagedAssembly(file)) {
                        Console.WriteLine($"Skipping non-managed assembly: {file}");
                        Log.Information($"Skipping {file}");
                        continue;
                    }
                    assembly = Assembly.LoadFile(file);
                    foreach (var type in assembly.GetExportedTypes()) {
                        if (!type.IsAbstract && type.IsSubclassOf(typeof(Phonemizer))) {
                            phonemizerFactories.Add(PhonemizerFactory.Get(type));
                        }
                    }
                } catch (Exception e) {
                    Console.WriteLine($"Failed to load plugin: {file}");
                    Log.Warning(e, $"Failed to load {file}.");
                    continue;
                }
            }
            foreach (var type in GetType().Assembly.GetExportedTypes()) {
                if (!type.IsAbstract && type.IsSubclassOf(typeof(Phonemizer))) {
                    phonemizerFactories.Add(PhonemizerFactory.Get(type));
                }
            }
            PhonemizerFactories = phonemizerFactories.OrderBy(factory => factory.tag).ToArray();
            stopWatch.Stop();
            Console.WriteLine($"Search all plugins completed in: {stopWatch.Elapsed}");
            Log.Information($"Search all plugins: {stopWatch.Elapsed}");
        }

        #region Command Queue

        readonly Deque<UCommandGroup> undoQueue = new Deque<UCommandGroup>();
        readonly Deque<UCommandGroup> redoQueue = new Deque<UCommandGroup>();
        UCommandGroup? undoGroup = null;
        UCommandGroup? savedPoint = null;
        UCommandGroup? autosavedPoint = null;

        public bool ChangesSaved {
            get {
                bool changesSaved = (Project.Saved || (Project.tracks.Count <= 1 && Project.parts.Count == 0)) &&
                    (undoQueue.Count > 0 && savedPoint == undoQueue.Last() || undoQueue.Count == 0 && savedPoint == null);
                Console.WriteLine($"ChangesSaved: {changesSaved}");
                return changesSaved;
            }
        }

        private void CrashSave() {
            try {
                if (Project == null) {
                    Console.WriteLine("Crash save skipped: Project is null.");
                    Log.Warning("Crash save project is null.");
                    return;
                }
                bool untitled = string.IsNullOrEmpty(Project.FilePath);
                if (untitled) {
                    Directory.CreateDirectory(PathManager.Inst.BackupsPath);
                    Console.WriteLine("Created backups directory for crash save.");
                }
                string dir = untitled
                    ? PathManager.Inst.BackupsPath
                    : Path.GetDirectoryName(Project.FilePath);
                string filename = untitled
                    ? "Untitled"
                    : Path.GetFileNameWithoutExtension(Project.FilePath);
                string backup = Path.Join(dir, filename + "-backup.ustx");
                Console.WriteLine($"Saving crash backup to {backup}.");
                Log.Information($"Saving backup {backup}.");
                Format.Ustx.Save(backup, Project);
                Console.WriteLine($"Crash backup saved to {backup}.");
                Log.Information($"Saved backup {backup}.");
            } catch (Exception e) {
                Console.WriteLine("Crash save failed: " + e.Message);
                Log.Error(e, "Save backup failed.");
            }
        }

        public void AutoSave() {
            if (Project == null) {
                Console.WriteLine("Autosave skipped: Project is null.");
                Log.Information("Autosave skipped.");
                return;
            }
            if (undoQueue.LastOrDefault() == autosavedPoint) {
                Console.WriteLine("Autosave skipped: No changes since last save.");
                Log.Information("Autosave skipped.");
                return;
            }
            try {
                bool untitled = string.IsNullOrEmpty(Project.FilePath);
                if (untitled) {
                    Directory.CreateDirectory(PathManager.Inst.BackupsPath);
                    Console.WriteLine("Autosave: Created backups directory.");
                }
                string dir = untitled
                    ? PathManager.Inst.BackupsPath
                    : Path.GetDirectoryName(Project.FilePath);
                string filename = untitled
                    ? "Untitled"
                    : Path.GetFileNameWithoutExtension(Project.FilePath);

                string backup = Path.Join(dir, filename + "-autosave.ustx");
                Console.WriteLine($"Autosaving project to {backup}. Current track count: {Project.tracks.Count}");
                Log.Information($"Autosave {backup}.");
                Format.Ustx.AutoSave(backup, Project);
                Console.WriteLine($"Autosave completed for {backup}. Track count: {Project.tracks.Count}");
                Log.Information($"Autosaved {backup}.");
                autosavedPoint = undoQueue.LastOrDefault();
            } catch (Exception e) {
                Console.WriteLine("Autosave failed: " + e.Message);
                Log.Error(e, "Autosave failed.");
            }
        }

        public void ExecuteCmd(UCommand cmd) {
            if (mainThread != Thread.CurrentThread) {
                if (!(cmd is ProgressBarNotification)) {
                    Console.WriteLine($"ExecuteCmd called on non-main thread: {cmd}");
                    Log.Warning($"{cmd} not on main thread");
                }
                PostOnUIThread(() => ExecuteCmd(cmd));
                return;
            }
            if (cmd is UNotification) {
                if (cmd is SaveProjectNotification saveProjectNotif) {
                    Console.WriteLine("Processing SaveProjectNotification...");
                    if (undoQueue.Count > 0) {
                        savedPoint = undoQueue.Last();
                    }
                    if (string.IsNullOrEmpty(saveProjectNotif.Path)) {
                        Console.WriteLine($"Saving project to {Project.FilePath}. Track count: {Project.tracks.Count}");
                        Format.Ustx.Save(Project.FilePath, Project);
                    } else {
                        Console.WriteLine($"Saving project to {saveProjectNotif.Path}. Track count: {Project.tracks.Count}");
                        Format.Ustx.Save(saveProjectNotif.Path, Project);
                    }
                } else if (cmd is LoadProjectNotification notification) {
                    Console.WriteLine("Processing LoadProjectNotification...");
                    undoQueue.Clear();
                    redoQueue.Clear();
                    undoGroup = null;
                    savedPoint = null;
                    autosavedPoint = null;
                    Project = notification.project;
                    playPosTick = 0;
                    Console.WriteLine($"Project loaded: {Project.name} with {Project.tracks.Count} tracks.");
                } else if (cmd is SetPlayPosTickNotification setPlayPosTickNotif) {
                    playPosTick = setPlayPosTickNotif.playPosTick;
                    Console.WriteLine($"Play position set to {playPosTick}.");
                } else if (cmd is SingersChangedNotification) {
                    Console.WriteLine("SingersChangedNotification received. Reloading singers...");
                    SingerManager.Inst.SearchAllSingers();
                } else if (cmd is ValidateProjectNotification) {
                    Console.WriteLine("Validating project...");
                    Project.ValidateFull();
                } else if (cmd is SingersRefreshedNotification || cmd is OtoChangedNotification) {
                    foreach (var track in Project.tracks) {
                        track.OnSingerRefreshed();
                    }
                    Project.ValidateFull();
                    if (cmd is OtoChangedNotification) {
                        Console.WriteLine("OtoChangedNotification processed. Pre-rendering...");
                        ExecuteCmd(new PreRenderNotification());
                    }
                }
                Publish(cmd);
                if (!cmd.Silent) {
                    Console.WriteLine($"Published notification {cmd}");
                    Log.Information($"Publish notification {cmd}");
                }
                return;
            }
            if (undoGroup == null) {
                Console.WriteLine($"No active UndoGroup for command: {cmd}");
                Log.Error($"No active UndoGroup {cmd}");
                return;
            }
            undoGroup.Commands.Add(cmd);
            lock (Project) {
                Console.WriteLine($"Executing command: {cmd}");
                cmd.Execute();
            }
            if (!cmd.Silent) {
                Console.WriteLine($"Executed command: {cmd}");
                Log.Information($"ExecuteCmd {cmd}");
            }
            Publish(cmd);
            if (!undoGroup.DeferValidate) {
                Console.WriteLine("Validating project after command execution...");
                Project.Validate(cmd.ValidateOptions);
            }
        }



        public void StartUndoGroup(bool deferValidate = false) {
            if (undoGroup != null) {
                Console.WriteLine("undoGroup already started. Ending previous group...");
                Log.Error("undoGroup already started");
                EndUndoGroup();
            }
            undoGroup = new UCommandGroup(deferValidate);
            Console.WriteLine("Started new undoGroup.");
            Log.Information("undoGroup started");
        }

        public void EndUndoGroup() {
            if (undoGroup == null) {
                Console.WriteLine("No active undoGroup to end.");
                Log.Error("No active undoGroup to end.");
                return;
            }
            if (undoGroup.Commands.Count > 0) {
                Console.WriteLine("Ending undoGroup with commands...");
                undoQueue.AddToBack(undoGroup);
                redoQueue.Clear();
            } else {
                Console.WriteLine("Ending empty undoGroup.");
            }
            while (undoQueue.Count > Util.Preferences.Default.UndoLimit) {
                undoQueue.RemoveFromFront();
            }
            if (undoGroup.DeferValidate) {
                Console.WriteLine("Validating project after deferred undoGroup...");
                Project.ValidateFull();
            }
            undoGroup.Merge();
            undoGroup = null;
            Console.WriteLine("undoGroup ended.");
            Log.Information("undoGroup ended");
            ExecuteCmd(new PreRenderNotification());
        }

        public void RollBackUndoGroup() {
            if (undoGroup == null) {
                Console.WriteLine("No active undoGroup to rollback.");
                Log.Error("No active undoGroup to rollback.");
                return;
            }
            Console.WriteLine("Rolling back undoGroup...");
            for (int i = undoGroup.Commands.Count - 1; i >= 0; i--) {
                var cmd = undoGroup.Commands[i];
                cmd.Unexecute();
                if (i == 0) {
                    Console.WriteLine("Validating project after rollback...");
                    Project.ValidateFull();
                }
                Publish(cmd, true);
            }
            undoGroup.Commands.Clear();
        }

        public void Undo() {
            if (undoQueue.Count == 0) {
                Console.WriteLine("No undo commands available.");
                return;
            }
            var group = undoQueue.RemoveFromBack();
            Console.WriteLine("Undoing command group...");
            for (int i = group.Commands.Count - 1; i >= 0; i--) {
                var cmd = group.Commands[i];
                cmd.Unexecute();
                if (i == 0) {
                    Console.WriteLine("Validating project after undo...");
                    Project.ValidateFull();
                }
                Publish(cmd, true);
            }
            redoQueue.AddToBack(group);
            ExecuteCmd(new PreRenderNotification());
        }

        public void Redo() {
            if (redoQueue.Count == 0) {
                Console.WriteLine("No redo commands available.");
                return;
            }
            var group = redoQueue.RemoveFromBack();
            Console.WriteLine("Redoing command group...");
            for (var i = 0; i < group.Commands.Count; i++) {
                var cmd = group.Commands[i];
                cmd.Execute();
                if (i == group.Commands.Count - 1) {
                    Console.WriteLine("Validating project after redo...");
                    Project.ValidateFull();
                }
                Publish(cmd);
            }
            undoQueue.AddToBack(group);
            ExecuteCmd(new PreRenderNotification());
        }

        # endregion

        # region Command Subscribers

        private readonly object lockObj = new object();
        private readonly List<ICmdSubscriber> subscribers = new List<ICmdSubscriber>();

        public void AddSubscriber(ICmdSubscriber sub) {
            lock (lockObj) {
                if (!subscribers.Contains(sub)) {
                    subscribers.Add(sub);
                    Console.WriteLine($"Subscriber added: {sub}");
                }
            }
        }

        public void RemoveSubscriber(ICmdSubscriber sub) {
            lock (lockObj) {
                if (subscribers.Contains(sub)) {
                    subscribers.Remove(sub);
                    Console.WriteLine($"Subscriber removed: {sub}");
                }
            }
        }

        private void Publish(UCommand cmd, bool isUndo = false) {
            lock (lockObj) {
                Console.WriteLine($"Publishing command: {cmd}");
                foreach (var sub in subscribers) {
                    sub.OnNext(cmd, isUndo);
                    Console.WriteLine($"Notified subscriber: {sub}");
                }
            }
        }

        #endregion
    }
}
