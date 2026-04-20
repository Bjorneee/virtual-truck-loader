using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using static System.Net.Mime.MediaTypeNames;
using Debug = UnityEngine.Debug;

public class PackingBackendClient : MonoBehaviour
{
    [Header("Server")]
    [SerializeField] private string baseUrl = "http://127.0.0.1:8000";
    [SerializeField] private string backendRelativePath = @"backend\backend.exe";
    [SerializeField] private bool autoStartServer = true;

    private Process _serverProcess;
    private string _backendExePath;
    private string _backendWorkingDirectory;

    public bool IsBackendReady { get; private set; }

    private void Awake()
    {
#if UNITY_EDITOR
        // In Editor, use the Unity project root as the base
        string projectRoot = Directory.GetCurrentDirectory();
        _backendExePath = Path.GetFullPath(Path.Combine(projectRoot, "../dist/backend/backend.exe"));
#else
        // In a build, Application.dataPath points to VTL_Data
        // Parent folder is the folder containing VTL.exe
        string buildRoot = Directory.GetParent(UnityEngine.Application.dataPath).FullName;
        _backendExePath = Path.GetFullPath(Path.Combine(buildRoot, backendRelativePath));
#endif

        _backendWorkingDirectory = Path.GetDirectoryName(_backendExePath);

        Debug.Log("Resolved backend exe path: " + _backendExePath);
        Debug.Log("Resolved backend working directory: " + _backendWorkingDirectory);
    }

    private void Start()
    {
        if (autoStartServer)
        {
            StartBackendServer();
            StartCoroutine(WaitForHealthThenLog());
        }
    }

    private void OnApplicationQuit()
    {
        StopBackendServer();
    }

    public void StartBackendServer()
    {
        Debug.Log("Starting local server...");

        if (_serverProcess != null && !_serverProcess.HasExited)
        {
            Debug.Log("Backend server already running.");
            return;
        }

        if (!File.Exists(_backendExePath))
        {
            Debug.LogError("backend.exe not found at: " + _backendExePath);
            return;
        }

        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = _backendExePath,
                Arguments = "",
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                WorkingDirectory = _backendWorkingDirectory,
            };

            _serverProcess = new Process();
            _serverProcess.StartInfo = startInfo;

            _serverProcess.OutputDataReceived += (sender, args) =>
            {
                if (!string.IsNullOrEmpty(args.Data))
                    Debug.Log("[FastAPI] " + args.Data);
            };

            _serverProcess.ErrorDataReceived += (sender, args) =>
            {
                if (!string.IsNullOrEmpty(args.Data))
                    Debug.LogWarning("[FastAPI ERR] " + args.Data);
            };

            _serverProcess.Start();
            _serverProcess.BeginOutputReadLine();
            _serverProcess.BeginErrorReadLine();

            Debug.Log("Started FastAPI backend process.");
            Debug.Log("Exe: " + _serverProcess.StartInfo.FileName);
            Debug.Log("Dir: " + _serverProcess.StartInfo.WorkingDirectory);
        }
        catch (Exception ex)
        {
            Debug.LogError("Failed to start backend server: " + ex);
        }
    }

    public void StopBackendServer()
    {
        try
        {
            if (_serverProcess != null && !_serverProcess.HasExited)
            {
                _serverProcess.Kill();
                _serverProcess.Dispose();
                _serverProcess = null;
                Debug.Log("Stopped FastAPI backend process.");
            }
        }
        catch (Exception ex)
        {
            Debug.LogWarning("Failed to stop backend cleanly: " + ex.Message);
        }
    }

    public IEnumerator WaitForHealthThenLog()
    {
        IsBackendReady = false;
        const float timeoutSeconds = 10f;
        float elapsed = 0f;

        while (elapsed < timeoutSeconds)
        {
            using var req = UnityWebRequest.Get($"{baseUrl.TrimEnd('/')}/health");
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success && req.responseCode == 200)
            {
                IsBackendReady = true;
                Debug.Log("Backend is healthy.");
                yield break;
            }

            elapsed += 0.5f;
            yield return new WaitForSeconds(0.5f);
        }

        Debug.LogWarning("Backend did not become healthy in time.");
    }

    public IEnumerator SendPackRequest(PackingRequest requestData, Action<PackingResponse> onSuccess = null, Action<string> onError = null)
    {
        string json = JsonUtility.ToJson(requestData, true);
        Debug.Log("Sending pack request:\n" + json);

        byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

        using var req = new UnityWebRequest($"{baseUrl.TrimEnd('/')}/pack", "POST");
        req.uploadHandler = new UploadHandlerRaw(bodyRaw);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");

        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            string msg = $"Pack request failed: {req.error} | HTTP {req.responseCode}\n{req.downloadHandler.text}";
            Debug.LogError(msg);
            onError?.Invoke(msg);
            yield break;
        }

        string responseJson = req.downloadHandler.text;
        Debug.Log("Received pack response:\n" + responseJson);

        PackingResponse response;
        try
        {
            response = JsonUtility.FromJson<PackingResponse>(responseJson);
        }
        catch (Exception ex)
        {
            string msg = "Failed to parse pack response JSON: " + ex.Message;
            Debug.LogError(msg);
            onError?.Invoke(msg);
            yield break;
        }

        onSuccess?.Invoke(response);
    }
}

[Serializable]
public class TruckData
{
    public string id;
    public float width;
    public float height;
    public float depth;
    public float max_weight;
}

[Serializable]
public class BoxData
{
    public string id;
    public float width;
    public float height;
    public float depth;
    public float weight;
    public bool rotatable;
    public float priority;
}

[Serializable]
public class PackingRequest
{
    public TruckData truck;
    public List<BoxData> boxes;
}

[Serializable]
public class PlacedBox
{
    public string id;
    public float x;
    public float y;
    public float z;
    public int rotation;
}

[Serializable]
public class PackingResponse
{
    public List<PlacedBox> placed;
    public List<BoxData> unplaced;
    public float utilization;
    public float runtime_ms;
    public List<string> notes;
}