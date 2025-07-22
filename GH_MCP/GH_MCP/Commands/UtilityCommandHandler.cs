using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using GrasshopperMCP.Models;
using Grasshopper.Kernel;
using Rhino;
using Rhino.Runtime;

namespace GrasshopperMCP.Commands
{
    /// <summary>
    /// Miscellaneous utility command handlers
    /// </summary>
    public static class UtilityCommandHandler
    {
        private static readonly Dictionary<string, string> MacroStore = new Dictionary<string, string>();
        private static readonly Dictionary<string, string> Snapshots = new Dictionary<string, string>();

        /// <summary>
        /// Execute a new solution to refresh preview
        /// </summary>
        public static object ExecutePreview(Command command)
        {
            object result = null;
            Exception exception = null;
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                        throw new InvalidOperationException("No active Grasshopper document");
                    doc.NewSolution(false);
                    result = new { success = true };
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in ExecutePreview: {ex.Message}");
                }
            }));
            while (result == null && exception == null)
                Thread.Sleep(10);
            if (exception != null)
                throw exception;
            return result;
        }

        /// <summary>
        /// Execute a Rhino script string
        /// </summary>
        public static object ExecuteScript(Command command)
        {
            string script = command.GetParameter<string>("script");
            if (string.IsNullOrEmpty(script))
                throw new ArgumentException("Script text is required");
            bool ok = RhinoApp.RunScript(script, false);
            return new { success = ok };
        }

        /// <summary>
        /// Store a Rhino command macro
        /// </summary>
        public static object CreateMacro(Command command)
        {
            string name = command.GetParameter<string>("name");
            string macro = command.GetParameter<string>("macro");
            if (string.IsNullOrEmpty(name) || string.IsNullOrEmpty(macro))
                throw new ArgumentException("Name and macro are required");
            MacroStore[name] = macro;
            return new { success = true, name };
        }

        /// <summary>
        /// Run a stored Rhino command macro
        /// </summary>
        public static object RunMacro(Command command)
        {
            string name = command.GetParameter<string>("name");
            string macro = command.GetParameter<string>("macro");
            if (!string.IsNullOrEmpty(name) && MacroStore.TryGetValue(name, out var stored))
                macro = stored;
            if (string.IsNullOrEmpty(macro))
                throw new ArgumentException("Macro not found");
            bool ok = RhinoApp.RunScript(macro, false);
            return new { success = ok };
        }

        /// <summary>
        /// Take a snapshot of the current document
        /// </summary>
        public static object Snapshot(Command command)
        {
            string name = command.GetParameter<string>("name") ?? Guid.NewGuid().ToString();
            object result = null;
            Exception exception = null;
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                        throw new InvalidOperationException("No active Grasshopper document");
                    var io = new GH_DocumentIO(doc);
                    string path = Path.GetTempFileName();
                    if (!io.Save(path))
                        throw new InvalidOperationException("Failed to save snapshot");
                    Snapshots[name] = path;
                    result = new { success = true, name };
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in Snapshot: {ex.Message}");
                }
            }));
            while (result == null && exception == null)
                Thread.Sleep(10);
            if (exception != null)
                throw exception;
            return result;
        }

        /// <summary>
        /// Revert to a previously taken snapshot
        /// </summary>
        public static object RevertSnapshot(Command command)
        {
            string name = command.GetParameter<string>("name");
            if (string.IsNullOrEmpty(name) || !Snapshots.TryGetValue(name, out var path))
                throw new ArgumentException("Snapshot not found");
            object result = null;
            Exception exception = null;
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    var io = new GH_DocumentIO();
                    if (!io.Open(path) || io.Document == null)
                        throw new InvalidOperationException("Failed to load snapshot");
                    var canvas = Grasshopper.Instances.ActiveCanvas;
                    if (canvas == null)
                        throw new InvalidOperationException("No active Grasshopper canvas");
                    canvas.Document = io.Document;
                    canvas.Document.NewSolution(false);
                    result = new { success = true, name };
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in RevertSnapshot: {ex.Message}");
                }
            }));
            while (result == null && exception == null)
                Thread.Sleep(10);
            if (exception != null)
                throw exception;
            return result;
        }

        /// <summary>
        /// Get preview geometry from a component
        /// </summary>
        public static object GetGeometry(Command command)
        {
            string idStr = command.GetParameter<string>("id");
            if (string.IsNullOrEmpty(idStr))
                throw new ArgumentException("Component ID is required");
            object result = null;
            Exception exception = null;
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    var doc = Grasshopper.Instances.ActiveCanvas?.Document;
                    if (doc == null)
                        throw new InvalidOperationException("No active Grasshopper document");
                    if (!Guid.TryParse(idStr, out var id))
                        throw new ArgumentException("Invalid component ID format");
                    var obj = doc.FindObject(id, true) as IGH_Component;
                    if (obj == null)
                        throw new ArgumentException("Component not found");
                    var outputs = new List<object>();
                    foreach (var param in obj.Params.Output)
                    {
                        var data = new List<string>();
                        foreach (var d in param.VolatileData.AllData(true))
                        {
                            var val = d.ScriptVariable();
                            data.Add(val != null ? val.ToString() : d.ToString());
                        }
                        outputs.Add(new { name = param.Name, data });
                    }
                    result = new { id = idStr, outputs };
                }
                catch (Exception ex)
                {
                    exception = ex;
                    RhinoApp.WriteLine($"Error in GetGeometry: {ex.Message}");
                }
            }));
            while (result == null && exception == null)
                Thread.Sleep(10);
            if (exception != null)
                throw exception;
            return result;
        }

        /// <summary>
        /// Run a Python script inside Rhino
        /// </summary>
        public static object RunGHPython(Command command)
        {
            string script = command.GetParameter<string>("script");
            if (string.IsNullOrEmpty(script))
                throw new ArgumentException("Python script is required");
            using (var py = PythonScript.Create())
            {
                py.ExecuteScript(script);
            }
            return new { success = true };
        }
    }
}
