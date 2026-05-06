using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;
using UnityEngine.UIElements;
using System.IO;
using UnityEngine.Networking;
using Debug = UnityEngine.Debug;
using System.Runtime.InteropServices;

public class UIManager : MonoBehaviour
{
    [SerializeField] private PackingBackendClient backendClient;

    public static UIManager Instance;

    private void Awake()
    {
        Instance = this;
    }

    [Header("Settings")]
    public VisualTreeAsset itemRowTemplate;
    public GameObject boxPrefab;
    public Transform spawnLocation;

    [Header("Truck Settings")]
    public GameObject truckFloorObject;
    public GameObject truckVolumeObject;
    private FloatField _truckL, _truckW, _truckH;

    // Force these to match the 3D axes exactly: L = X, W = Z
    public float TruckX => _truckL != null ? _truckL.value : 1f;
    public float TruckZ => _truckW != null ? _truckW.value : 1f;
    public float TruckY => _truckH != null ? _truckH.value : 1f;

    // UI Elements
    private ListView _itemListView;

    private Button _btnAdd;
    private FloatField _inputLength;
    private FloatField _inputWidth;
    private FloatField _inputHeight;
    private FloatField _inputWeight;
    private Toggle _toggleStackable;
    private DropdownField _inputGroup;

    private Button _btnSave;
    private List<GameObject> _visualBoxes = new List<GameObject>();
    private Button _btnLoad;
    private Button _btnFile;
    private Button _btnAddMenu;
    private Button _btnSort;
    private Button _btnView;

    private Dictionary<string, GameObject> _itemObjects = new Dictionary<string, GameObject>();

    private Button _btnSettings;
    private Button _btnCloseSettings;
    private VisualElement _settingsOverlay;

    private Label _lblWeight;
    private Label _lblVolume;
    private ProgressBar _barVolume;
    private CargoItem _currentlySelectedItem = null;

    private Button _btnGenerate;
    private VisualElement _loadingOverlay;

    private DropdownField _inputAlgorithm;
    private SliderInt _inputTimeLimit;

    private Button _btnClearList;
    private Button _btnBack;
    private TextField _inputItemName;

    [Header("Camera Angles")]
    public Transform mainCamera;
    public Vector3 isoPos, isoRot;
    public Vector3 topPos, topRot;
    public Vector3 sidePos, sideRot;
    private int _currentViewIndex = 0;
    public CameraController cameraControl;

    private List<CargoItem> _inventory = new List<CargoItem>();

    public float TruckL => _truckL != null ? _truckL.value : 1f;
    public float TruckW => _truckW != null ? _truckW.value : 1f;
    public float TruckH => _truckH != null ? _truckH.value : 1f;

    [Header("3D Preview Setup")]
    public Transform previewSpawnPoint;
    private GameObject _previewBox3D;

    private void OnEnable()
    {
        var root = GetComponent<UIDocument>().rootVisualElement;

        _btnAdd = root.Q<Button>("BtnAdd");
        _inputLength = root.Q<FloatField>("InputLength");
        _inputWidth = root.Q<FloatField>("InputWidth");
        _inputHeight = root.Q<FloatField>("InputHeight");
        _inputWeight = root.Q<FloatField>("InputWeight");
        _toggleStackable = root.Q<Toggle>("ToggleStackable");
        _btnSave = root.Q<Button>("BtnSave");
        _btnLoad = root.Q<Button>("BtnLoad");
        _btnFile = root.Q<Button>("BtnFile");
        _btnAddMenu = root.Q<Button>("BtnAddMenu");
        _btnView = root.Q<Button>("BtnView");
        _btnSort = root.Q<Button>("BtnSort");

        _truckL = root.Q<FloatField>("TruckL");
        _truckW = root.Q<FloatField>("TruckW");
        _truckH = root.Q<FloatField>("TruckH");
        _lblWeight = root.Q<Label>("LblWeight");
        _lblVolume = root.Q<Label>("LblVolume");
        _barVolume = root.Q<ProgressBar>("BarVolume");
        _inputGroup = root.Q<DropdownField>("InputGroup");
        _inputItemName = root.Q<TextField>("InputItemName");

        _btnGenerate = root.Q<Button>("BtnGenerate");
        _loadingOverlay = root.Q<VisualElement>("LoadingOverlay");
        if (_btnGenerate != null) _btnGenerate.clicked += OnGenerateClicked;

        _btnSettings = root.Q<Button>("BtnSettings");
        _btnCloseSettings = root.Q<Button>("BtnCloseSettings");
        _settingsOverlay = root.Q<VisualElement>("SettingsOverlay");

        _inputAlgorithm = root.Q<DropdownField>("InputAlgorithm");
        _inputTimeLimit = root.Q<SliderInt>("InputTimeLimit");

        if (_inputItemName != null) _inputItemName.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputLength != null) _inputLength.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputWidth != null) _inputWidth.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputHeight != null) _inputHeight.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputWeight != null) _inputWeight.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_toggleStackable != null) _toggleStackable.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputGroup != null) _inputGroup.RegisterValueChangedCallback(evt => OnInputChanged());

        _btnClearList = root.Q<Button>("BtnClearList");
        if (_btnClearList != null) _btnClearList.clicked += ClearAll;

        if (_btnSettings != null) _btnSettings.clicked += OpenSettings;
        if (_btnCloseSettings != null) _btnCloseSettings.clicked += CloseSettings;

        _btnBack = root.Q<Button>("BtnBack");
        if (_btnBack != null) _btnBack.clicked += OnBackClicked;

        _itemListView = root.Q<ListView>("ItemListView");
        ConfigureListView();

        if (_btnAdd != null) _btnAdd.clicked += OnAddClicked;
        if (_btnSave != null) _btnSave.clicked += OnSaveClicked;
        if (_btnLoad != null) _btnLoad.clicked += OnLoadClicked;
        if (_btnFile != null) _btnFile.clicked += OnFileClicked;
        if (_btnAddMenu != null) _btnAddMenu.clicked += OnAddMenuClicked;
        if (_btnView != null) _btnView.clicked += OnViewClicked;
        if (_btnSort != null) _btnSort.clicked += OnSortClicked;

        _truckL.RegisterValueChangedCallback(evt => UpdateTruckSize());
        _truckW.RegisterValueChangedCallback(evt => UpdateTruckSize());
        _truckH.RegisterValueChangedCallback(evt => UpdateTruckSize());

        if (previewSpawnPoint != null)
        {
            _previewBox3D = Instantiate(boxPrefab, previewSpawnPoint.position, Quaternion.identity);
            var dragScript = _previewBox3D.GetComponent("IsometricObjectDrag");
            if (dragScript != null) Destroy(dragScript);
            Destroy(_previewBox3D.GetComponent<Rigidbody>());
            Destroy(_previewBox3D.GetComponent<BoxCollider>());
        }

        _itemListView.RegisterCallback<PointerUpEvent>(evt =>
        {
            if (_itemListView.selectedIndex == -1)
            {
                SetRightPanelToCreateMode();
                if (_currentlySelectedItem != null) Deselect3DBox();
                _currentlySelectedItem = null;
                return;
            }

            CargoItem clickedItem = _inventory[_itemListView.selectedIndex];

            if (_currentlySelectedItem == clickedItem)
            {
                _itemListView.ClearSelection();
                SetRightPanelToCreateMode();
                Deselect3DBox();
                _currentlySelectedItem = null;
            }
            else
            {
                List<object> selection = new List<object> { clickedItem };
                OnItemSelected(selection);
            }
        });

        var leftPanel = root.Q<VisualElement>("LeftPanel");
        var rightPanel = root.Q<VisualElement>("RightPanel");

        if (leftPanel != null)
        {
            leftPanel.RegisterCallback<PointerDownEvent>(evt =>
            {
                var targetName = (evt.target as VisualElement)?.name;
                if (targetName == "LeftPanel" || targetName == "ItemListView")
                {
                    _itemListView.ClearSelection();
                }
            });
        }

        if (rightPanel != null)
        {
            rightPanel.RegisterCallback<PointerDownEvent>(evt =>
            {
                if ((evt.target as VisualElement)?.name == "RightPanel")
                {
                    _itemListView.ClearSelection();
                }
            });
        }

        // FIX 1: Set Default Truck Size so math doesn't fail on launch
        _truckL.SetValueWithoutNotify(6.0f);
        _truckW.SetValueWithoutNotify(2.4f);
        _truckH.SetValueWithoutNotify(2.6f);
        UpdateTruckSize();

        SetAppMode(true);
        UpdateRightPanelState(true);
        SetRightPanelToCreateMode();
    }

    private void ConfigureListView()
    {
        _itemListView.makeItem = () => itemRowTemplate.Instantiate();

        _itemListView.bindItem = (element, index) =>
        {
            var item = _inventory[index];
            var nameLabel = element.Q<Label>("ItemName");
            var sizeLabel = element.Q<Label>("ItemSize");

            nameLabel.text = item.Name;
            sizeLabel.text = $"{item.Length} x {item.Width} x {item.Height}";

            var btnRemove = element.Q<Button>("BtnRemove");
            btnRemove.clicked -= () => RemoveItem(item);
            btnRemove.clicked += () => RemoveItem(item);
        };

        _itemListView.itemsSource = _inventory;
        _itemListView.fixedItemHeight = 40;
    }

    private void OnAddClicked()
    {
        if (_currentlySelectedItem != null)
        {
            _itemListView.ClearSelection();
            SetRightPanelToCreateMode();
            return;
        }

        float l = _inputLength.value;
        float w = _inputWidth.value;
        float h = _inputHeight.value;
        float weight = _inputWeight.value;
        bool isStackable = _toggleStackable.value;
        string group = _inputGroup != null ? _inputGroup.value : "Standard";

        string currentInputText = _inputItemName != null ? _inputItemName.value : "";
        string finalName = "";

        if (string.IsNullOrWhiteSpace(currentInputText) || currentInputText == "New Box")
        {
            finalName = $"Box {_inventory.Count + 1}";
        }
        else
        {
            finalName = currentInputText;
        }

        if (l <= 0 || w <= 0 || h <= 0) return;

        var newItem = new CargoItem(finalName, l, w, h, weight, isStackable, group);

        _inventory.Add(newItem);
        //SpawnVisualBox(newItem);

        _itemListView.ClearSelection();
        SetRightPanelToCreateMode();

        _itemListView.RefreshItems();
        UpdateMetrics();
    }

    private void SpawnVisualBox(CargoItem item)
    {
        // 1. SMART RANDOM SPAWN
        // Keep them strictly inside the truck bounds
        float halfX = Mathf.Max(0, (TruckX / 2f) - (item.Length / 2f));
        float halfZ = Mathf.Max(0, (TruckZ / 2f) - (item.Width / 2f));

        float randX = Random.Range(-halfX, halfX);
        float randZ = Random.Range(-halfZ, halfZ);

        // Spawn slightly higher based on box count so they don't perfectly overlap
        float spawnY = (item.Height / 2f) + (_visualBoxes.Count * 0.05f);

        Vector3 spawnPos = new Vector3(randX, spawnY, randZ);

        // If loading from a save file, use the saved position instead!
        if (item.Position != Vector3.zero)
        {
            spawnPos = item.Position;
        }

        // 2. CREATE THE BOX
        GameObject newBox = Instantiate(boxPrefab, spawnPos, Quaternion.identity);
        newBox.transform.localScale = new Vector3(item.Length, item.Height, item.Width);

        // Apply saved rotation if loading, otherwise default
        if (item.Rotation != Quaternion.identity && item.Rotation.eulerAngles != Vector3.zero)
        {
            newBox.transform.rotation = item.Rotation;
        }

        SetBoxColor(newBox, item.DisplayColor);

        // Remove the old IsometricObjectDrag script if present
        var oldDragScript = newBox.GetComponent<IsometricObjectDrag>();
        if (oldDragScript != null) Destroy(oldDragScript);

        // 3. SET TO BRICK MODE
        Rigidbody rb = newBox.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.isKinematic = true;
            rb.useGravity = false;
        }

        _visualBoxes.Add(newBox);
        if (!string.IsNullOrEmpty(item.Id)) _itemObjects[item.Id] = newBox;
    }

    private void OnSaveClicked()
    {
        // 1. Sync Box Positions
        foreach (CargoItem item in _inventory)
        {
            if (_itemObjects.TryGetValue(item.Id, out GameObject box) && box != null)
            {
                item.Position = box.transform.position;
            }
        }

        // 2. Prepare Data
        InventoryData data = new InventoryData();
        data.items = _inventory;
        data.TruckLength = _truckL.value;
        data.TruckWidth = _truckW.value;
        data.TruckHeight = _truckH.value;
        data.AlgorithmPreference = _inputAlgorithm != null ? _inputAlgorithm.value : "Standard";
        data.MaxCalculationTime = _inputTimeLimit != null ? _inputTimeLimit.value : 10;

        string json = JsonUtility.ToJson(data, true);

        // 3. Open Windows Save Window
        OpenFileName ofn = new OpenFileName();
        ofn.structSize = Marshal.SizeOf(ofn);
        ofn.filter = "JSON Files\0*.json\0All Files\0*.*\0";
        ofn.file = new string(new char[256]);
        ofn.maxFile = ofn.file.Length;
        ofn.fileTitle = new string(new char[64]);
        ofn.maxFileTitle = ofn.fileTitle.Length;
        ofn.initialDir = UnityEngine.Application.dataPath;
        ofn.title = "Save Loadout";
        ofn.defExt = "json";
        ofn.flags = 0x00000002 | 0x00000004; // OFN_OVERWRITEPROMPT | OFN_HIDEREADONLY

        if (GetSaveFileName(ofn))
        {
            File.WriteAllText(ofn.file, json);
            Debug.Log($"<color=cyan>SAVED JSON to:</color> {ofn.file}");
        }
    }

    //Currently Obsolete/ used for debugging with file read/write instead of backend calls. Can be re-purposed for "Export JSON" button if desired.

    // private void WritePackRequestJSON()
    // {
    //     PackRequestData request = new PackRequestData();
    //     request.TruckLength = _truckL.value;
    //     request.TruckWidth = _truckW.value;
    //     request.TruckHeight = _truckH.value;
    //     request.items = new List<PackRequestItem>();

    //     foreach (CargoItem item in _inventory)
    //     {
    //         PackRequestItem requestedItem = new PackRequestItem
    //         {
    //             Id = item.Id,
    //             Length = item.Length,
    //             Width = item.Width,
    //             Height = item.Height,
    //             Weight = item.Weight,
    //         };

    //         request.items.Add(requestedItem);

    //         Debug.Log($"ITEM PACK REQUEST: -> {item.Name} | ID={item.Id} | L={item.Length}, W={item.Width}, H={item.Height}, Weight={item.Weight}");
    //     }

    //     //write JSON
    //     string requestJson = JsonUtility.ToJson(request, true);
    //     string requestPath = Path.Combine(Application.persistentDataPath, "pack_request.json");
    //     File.WriteAllText(requestPath, requestJson);

    //     Debug.Log($"<color=cyan>PACK REQUEST SAVED to:</color> {requestPath}");
    // }

    // private void WritePackResponseJSON()
    // {
    //     //Read backend response JSON
    //     string responsePath = Path.Combine(Application.persistentDataPath, "pack_response.json");

    //     if (!File.Exists(responsePath))
    //     {
    //         Debug.LogWarning($"No pack response file found at: {responsePath}");
    //         return;
    //     }

    //     string responseJson = File.ReadAllText(responsePath);
    //     PackResponseData response = JsonUtility.FromJson<PackResponseData>(responseJson);

    //     if (response == null || response.items == null)
    //     {
    //         Debug.LogError("Invalid pack response JSON.");
    //         return;
    //     }

    //     //Apply returned positions
    //     foreach (PackResponseItem responseItem in response.items)
    //     {
    //         if (_itemObjects.TryGetValue(responseItem.Id, out GameObject box))
    //         {
    //             box.transform.position = responseItem.Position;

    //             CargoItem item = _inventory.Find(x => x.Id == responseItem.Id);
    //             if (item != null)
    //             {
    //                 item.Position = responseItem.Position;
    //                 item.Rotation = responseItem.Rotation;
    //             }

    //             Debug.Log($"SORT RESPONSE -> ID={responseItem.Id} moved to {responseItem.Position}");
    //         }
    //         else
    //         {
    //             Debug.LogWarning($"No spawned box found for backend item ID: {responseItem.Id}");
    //         }
    //     }

    //     Debug.Log("<color=green>PACK RESPONSE APPLIED</color>");
    // }

    private PackingRequest BuildPackingRequest()
{
    var request = new PackingRequest
    {
        truck = new TruckData
        {
            id = "T1",
            width = _truckW.value,
            height = _truckH.value,
            depth = _truckL.value
        },
        boxes = new List<BoxData>()
    };

    foreach (CargoItem item in _inventory)
    {
        request.boxes.Add(new BoxData
        {
            id = item.Id,
            width = item.Width,
            height = item.Height,
            depth = item.Length,
            weight = item.Weight,
            rotatable = true,
            priority = 0f
        });

        Debug.Log($"Pack item -> {item.Name} | id={item.Id} | W={item.Width} H={item.Height} D={item.Length} WT={item.Weight}");
    }

    return request;
}

    private void OnSortClicked()
    {
        if (backendClient == null || !backendClient.IsBackendReady)
        {
        Debug.LogWarning("Backend is not ready yet.");
        return;
        }
        
        PackingRequest request = BuildPackingRequest();
        StartCoroutine(backendClient.SendPackRequest(
            BuildPackingRequest(),
            OnPackSuccess,
            OnPackError
        ));

        // WritePackRequestJSON();
        // WritePackResponseJSON();

    }

    private void ClearAll()
    {
        _itemListView.ClearSelection();

        foreach (GameObject box in _visualBoxes) Destroy(box);
        _visualBoxes.Clear();
        _inventory.Clear();
        _itemObjects.Clear();

        _itemListView.RefreshItems();
        UpdateMetrics();
    }


    private void OnPackSuccess(PackingResponse response)
    {
        if (response == null)
        {
            Debug.LogError("Pack response was null.");
            return;
        }

        if (response.placed != null)
        {
            SetAppMode(false);

            foreach (var placed in response.placed)
            {
                CargoItem item = _inventory.Find(i => i.Id == placed.id);
                if (item == null)
                {
                    Debug.LogWarning($"No CargoItem found for id {placed.id}");
                    continue;
                }

                bool rotated = placed.rotation == 1;

                float halfX = rotated ? item.Width / 2f : item.Length / 2f;
                float halfZ = rotated ? item.Length / 2f : item.Width / 2f;

                // backend: x = width axis, z = depth axis
                // unity:   z = width axis, x = length/depth axis
                Vector3 newPos = new Vector3(
                    placed.z + halfX,
                    placed.y + item.Height / 2f,
                    placed.x + halfZ
                );

                item.Position = newPos;
                item.Rotation = rotated ? Quaternion.Euler(0f, 90f, 0f) : Quaternion.identity;

                if (_itemObjects.TryGetValue(placed.id, out GameObject existingBox) && existingBox != null)
                {
                    existingBox.transform.position = newPos;
                }
                else
                {
                    SpawnVisualBox(item);
                }

                Debug.Log($"Placed {placed.id} at {newPos}, rotation={placed.rotation}");
                if (_itemObjects.TryGetValue(placed.id, out GameObject spawned) && spawned != null)
                    spawned.transform.rotation = item.Rotation;
            }
        }


        Debug.Log($"Packing complete. Utilization={response.utilization}, runtime_ms={response.runtime_ms}, notes={response.notes}");
    }

    private void OnPackError(string error)
    {
        Debug.LogError("Packing backend error: " + error);
    }


    private void OnLoadClicked()
    {
        // 1. Open Windows Load Window
        OpenFileName ofn = new OpenFileName();
        ofn.structSize = Marshal.SizeOf(ofn);
        ofn.filter = "JSON Files\0*.json\0All Files\0*.*\0";
        ofn.file = new string(new char[256]);
        ofn.maxFile = ofn.file.Length;
        ofn.fileTitle = new string(new char[64]);
        ofn.maxFileTitle = ofn.fileTitle.Length;
        ofn.initialDir = UnityEngine.Application.dataPath;
        ofn.title = "Load Loadout";
        ofn.defExt = "json";
        ofn.flags = 0x00000008; // OFN_FILEMUSTEXIST

        if (GetOpenFileName(ofn))
        {
            string path = ofn.file;
            string json = File.ReadAllText(path);

            ClearAll();

            InventoryData loadedData = JsonUtility.FromJson<InventoryData>(json);
            _truckL.value = loadedData.TruckLength;
            _truckW.value = loadedData.TruckWidth;
            _truckH.value = loadedData.TruckHeight;

            foreach (CargoItem item in loadedData.items)
            {
                _inventory.Add(item);
                SpawnVisualBox(item);
            }

            _itemListView.RefreshItems();
            UpdateMetrics();

            Debug.Log($"<color=green>LOADED:</color> {loadedData.items.Count} items from {path}");
        }
    }

    private void UpdateTruckSize()
    {
        if (_truckL == null || _truckW == null || _truckH == null) return;

        // 1. Get the values
        float xSize = Mathf.Clamp(_truckL.value, 1f, 100f); // Length -> X
        float zSize = Mathf.Clamp(_truckW.value, 1f, 100f); // Width -> Z
        float ySize = Mathf.Clamp(_truckH.value, 1f, 100f); // Height -> Y

        // 2. Sync UI fields
        _truckL.SetValueWithoutNotify(xSize);
        _truckW.SetValueWithoutNotify(zSize);
        _truckH.SetValueWithoutNotify(ySize);

        // 1. Scale the Solid Floor (Always thin)
        truckFloorObject.transform.localScale = new Vector3(xSize, 0.1f, zSize);
        // Keep the back-left corner at Y = 0
        truckFloorObject.transform.position = new Vector3(xSize/2, 0, zSize/2);

        // 4. Position and Scale the Glass Volume
        if (truckVolumeObject != null)
        {
            truckVolumeObject.transform.localScale = new Vector3((xSize + 0.01f), (ySize + 0.01f), (zSize + 0.01f));

            // Unity scales from the center. If height is 10, it goes 5 up and 5 down.
            // We move it up by (Height / 2) so the bottom of the glass touches the floor.
            truckVolumeObject.transform.position = new Vector3(xSize/2, ySize/2f, zSize/2);
        }
    }
    private void RemoveItem(CargoItem itemToRemove)
    {
        _inventory.Remove(itemToRemove);
        if (!string.IsNullOrEmpty(itemToRemove.Id)) _itemObjects.Remove(itemToRemove.Id);

        foreach (GameObject box in _visualBoxes) Destroy(box);
        _visualBoxes.Clear();

        foreach (var item in _inventory) SpawnVisualBox(item);

        _itemListView.RefreshItems();
        UpdateMetrics();
    }

    private void OnFileClicked()
    {
        ClearAll();
        Debug.Log("Scene Reset (New File)");
    }

    private void OnAddMenuClicked()
    {
        // 1. DYNAMIC SCALING
        // Make the boxes between 10% and 30% of the current truck dimensions.
        // We use Mathf.Max to ensure they never spawn smaller than 0.2 meters.
        float minL = Mathf.Max(0.2f, TruckX * 0.1f);
        float maxL = Mathf.Max(0.5f, TruckX * 0.3f);

        float minW = Mathf.Max(0.2f, TruckZ * 0.1f);
        float maxW = Mathf.Max(0.5f, TruckZ * 0.3f);

        float minH = Mathf.Max(0.2f, TruckY * 0.1f);
        float maxH = Mathf.Max(0.5f, TruckY * 0.3f);

        float rL = Mathf.Round(Random.Range(minL, maxL) * 10f) / 10f;
        float rW = Mathf.Round(Random.Range(minW, maxW) * 10f) / 10f;
        float rH = Mathf.Round(Random.Range(minH, maxH) * 10f) / 10f;
        float rWeight = Mathf.Round(Random.Range(5f, 25f) * 10f) / 10f;

        // 2. RANDOM GROUPS (For a colorful demo)
        string[] groups = { "Standard", "Fragile", "Heavy", "Electronics" };
        string randomGroup = groups[Random.Range(0, groups.Length)];

        // 3. CREATE THE ITEM
        CargoItem randomItem = new CargoItem($"AutoBox {_inventory.Count + 1}", rL, rW, rH, rWeight, true, randomGroup);

        if (string.IsNullOrEmpty(randomItem.Id)) randomItem.Id = System.Guid.NewGuid().ToString();

        _inventory.Add(randomItem);
        SpawnVisualBox(randomItem);
        _itemListView.RefreshItems();
        UpdateMetrics();
    }

    private void OnViewClicked()
    {
        if (cameraControl == null) return;

        _currentViewIndex++;
        if (_currentViewIndex > 2) _currentViewIndex = 0;

        switch (_currentViewIndex)
        {
            case 0: // ISOMETRIC (Looking down at an angle)
                cameraControl.SetViewAngle(35f, 45f);
                break;
            case 1: // TOP DOWN (Looking straight down from the sky)
                cameraControl.SetViewAngle(89.9f, 0f);
                break;
            case 2: // SIDE VIEW (Looking flat from the right side)
                cameraControl.SetViewAngle(0f, 90f);
                break;
        }
    }

    private void UpdateMetrics()
    {
        if (_lblWeight == null || _lblVolume == null) return;
        if (_truckL == null || _truckW == null || _truckH == null) return;

        float truckL = _truckL.value;
        float truckW = _truckW.value;
        float truckH = _truckH.value;

        if (truckL <= 0 || truckW <= 0 || truckH <= 0) return;

        float maxVolume = truckL * truckW * truckH;
        float currentVolume = 0f;
        float currentWeight = 0f;

        foreach (var item in _inventory)
        {
            currentVolume += (item.Length * item.Width * item.Height);
            currentWeight += item.Weight;
        }

        float fillPercentage = (currentVolume / maxVolume) * 100f;

        _lblWeight.text = $"Total Weight: {currentWeight:F1} kg";
        _lblVolume.text = $"Volume Used: {fillPercentage:F1}%";

        if (_barVolume != null) _barVolume.value = fillPercentage;

        if (fillPercentage > 100f)
        {
            _lblVolume.style.color = Color.red;
            if (_btnGenerate != null)
            {
                _btnGenerate.SetEnabled(false);
                _btnGenerate.style.backgroundColor = new Color(0.8f, 0.2f, 0.2f);
            }
        }
        else
        {
            _lblVolume.style.color = Color.white;
            if (_btnGenerate != null)
            {
                _btnGenerate.SetEnabled(_inventory.Count > 0);
                _btnGenerate.style.backgroundColor = new Color(0.18f, 0.54f, 0.34f);
            }
        }
    }

    private void OnItemSelected(System.Collections.Generic.IEnumerable<object> selectedItems)
    {
        for (int i = 0; i < _visualBoxes.Count; i++)
        {
            SetBoxColor(_visualBoxes[i], _inventory[i].DisplayColor);
        }

        var enumerator = selectedItems.GetEnumerator();

        if (!enumerator.MoveNext())
        {
            _currentlySelectedItem = null;
            SetRightPanelToCreateMode();
            return;
        }

        CargoItem selectedData = (CargoItem)enumerator.Current;
        _currentlySelectedItem = selectedData;

        int selectedIndex = _inventory.IndexOf(selectedData);
        if (selectedIndex >= 0 && selectedIndex < _visualBoxes.Count)
        {
            SetBoxColor(_visualBoxes[selectedIndex], Color.cyan);
        }

        if (_inputItemName != null) _inputItemName.SetValueWithoutNotify(selectedData.Name);
        _inputLength.SetValueWithoutNotify(selectedData.Length);
        _inputWidth.SetValueWithoutNotify(selectedData.Width);
        _inputHeight.SetValueWithoutNotify(selectedData.Height);
        _inputWeight.SetValueWithoutNotify(selectedData.Weight);
        _toggleStackable.SetValueWithoutNotify(selectedData.IsStackable);
        if (_inputGroup != null) _inputGroup.SetValueWithoutNotify(selectedData.GroupName);

        for (int i = 0; i < _visualBoxes.Count; i++)
        {
            Rigidbody rb = _visualBoxes[i].GetComponent<Rigidbody>();
            if (rb != null) rb.isKinematic = true; // Set everyone to brick mode
        }

        if (_currentlySelectedItem != null)
        {
            int index = _inventory.IndexOf(_currentlySelectedItem);
            Rigidbody selectedRb = _visualBoxes[index].GetComponent<Rigidbody>();
            if (selectedRb != null) selectedRb.isKinematic = false; // Only the selected one is "alive"
        }

        UpdateRightPanelState(true);
        Update3DPreview();

    }

    private void OnInputChanged()
    {
        Update3DPreview();

        float l = _inputLength.value;
        float w = _inputWidth.value;
        float h = _inputHeight.value;

        bool isInvalid = (l <= 0 || l > 100 || w <= 0 || w > 100 || h <= 0 || h > 100);

        if (isInvalid)
        {
            if (_btnAdd != null)
            {
                _btnAdd.SetEnabled(false);
                _btnAdd.style.backgroundColor = Color.red;
            }
            return;
        }
        else
        {
            if (_btnAdd != null)
            {
                _btnAdd.SetEnabled(true);
                _btnAdd.style.backgroundColor = new Color(0.14f, 0.44f, 1.0f);
            }
        }

        if (_currentlySelectedItem == null) return;

        if (_inputItemName != null) _currentlySelectedItem.Name = _inputItemName.value;
        _currentlySelectedItem.Length = l;
        _currentlySelectedItem.Width = w;
        _currentlySelectedItem.Height = h;
        _currentlySelectedItem.Weight = _inputWeight.value;
        _currentlySelectedItem.IsStackable = _toggleStackable.value;

        if (_inputGroup != null)
        {
            _currentlySelectedItem.GroupName = _inputGroup.value;
            _currentlySelectedItem.DisplayColor = CargoItem.GetColorForGroup(_inputGroup.value);
        }

        int index = _inventory.IndexOf(_currentlySelectedItem);
        if (index >= 0 && index < _visualBoxes.Count)
        {
            GameObject boxToResize = _visualBoxes[index];
            boxToResize.transform.localScale = new Vector3(_currentlySelectedItem.Length, _currentlySelectedItem.Height, _currentlySelectedItem.Width);
            SetBoxColor(boxToResize, _currentlySelectedItem.DisplayColor);
        }

        _itemListView.RefreshItems();
        UpdateMetrics();
    }

    public void SetSelectionFrom3D(GameObject clickedBox)
    {
        int index = _visualBoxes.IndexOf(clickedBox);
        if (index != -1)
        {
            CargoItem clickedItem = _inventory[index];

            // FIX: If it is ALREADY selected, do nothing! Just let the user drag it.
            // (They can deselect by clicking the empty background instead).
            if (_currentlySelectedItem != clickedItem)
            {
                _itemListView.SetSelectionWithoutNotify(new List<int> { index });

                List<object> selection = new List<object> { clickedItem };
                OnItemSelected(selection);
            }
        }
    }

    public void ClearSelectionFrom3D()
    {
        _itemListView.ClearSelection();
        SetRightPanelToCreateMode();

        if (_currentlySelectedItem != null)
        {
            Deselect3DBox();
            _currentlySelectedItem = null;
        }
    }

    private void OpenSettings()
    {
        if (_settingsOverlay != null) _settingsOverlay.style.display = DisplayStyle.Flex;
    }

    private void CloseSettings()
    {
        if (_settingsOverlay != null) _settingsOverlay.style.display = DisplayStyle.None;
    }

    private void OnGenerateClicked()
    {
        if (backendClient == null || !backendClient.IsBackendReady)
        {
        Debug.LogWarning("Backend is not ready yet.");
        return;
        }

        // Prevent clicking if there are no boxes
        if (_inventory.Count == 0)
        {
            Debug.LogWarning("Cannot generate: Truck is empty!");
            return;
        }

        // Start the fake waiting process
        StartCoroutine(backendClient.SendPackRequest(BuildPackingRequest(), OnPackSuccess, OnPackError));
    }
    /*
    private System.Collections.IEnumerator MockAPICallRoutine()
    {
        if (_loadingOverlay != null) _loadingOverlay.style.display = DisplayStyle.Flex;

        // --- NEW: TRANSLATION LOGIC ---
        // 1. Build the Truck object for Python
        API_Truck apiTruck = new API_Truck();
        apiTruck.width = _truckW.value;   // Mapping Unity Width to Python width
        apiTruck.height = _truckH.value;  // Mapping Unity Height to Python height
        apiTruck.depth = _truckL.value;   // Mapping Unity Length to Python depth

        // 2. Build the List of Boxes for Python
        List<API_Box> apiBoxes = new List<API_Box>();
        foreach (var item in _inventory)
        {
            apiBoxes.Add(new API_Box
            {
                id = item.Id,
                width = item.Width,
                height = item.Height,
                depth = item.Length,
                weight = item.Weight
            });
        }

        // 3. Wrap it all into the final Request
        API_PackingRequest packingRequest = new API_PackingRequest();
        packingRequest.truck = apiTruck;
        packingRequest.boxes = apiBoxes;

        string jsonData = JsonUtility.ToJson(packingRequest);
        Debug.Log("Sending to Python: " + jsonData);
        // ------------------------------

        using (UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:8000/pack", "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Destroy(rb); // Remove physics entirely for the result view
            }

            // B. Move the box to its new "Calculated" coordinate
            // We add Height/2 because Unity objects spawn from their center, not the bottom
            box.transform.position = new Vector3(currentX, item.Height / 2f, currentZ);

            // C. Increment the coordinates so the next box goes next to it
            currentZ += item.Length + 0.2f; // Add a tiny gap
            currentX += item.Width + 0.2f;
        }

        Debug.Log("Boxes snapped to final positions!");
    } */
    // True = Show List, False = Show 3D Truck
    public void SetAppMode(bool isInventoryMode)
    {
        var leftPanel = GetComponent<UIDocument>().rootVisualElement.Q<VisualElement>("LeftPanel");
        var centerView = GetComponent<UIDocument>().rootVisualElement.Q<VisualElement>("CenterView");

        if (isInventoryMode)
        {
            if (leftPanel != null)
            {
                leftPanel.style.display = DisplayStyle.Flex;

                // NEW: Force the Left Panel to stretch across the empty middle screen!
                leftPanel.style.flexGrow = 1;
            }
            if (centerView != null) centerView.style.display = DisplayStyle.None;
        }
        else
        {
            if (leftPanel != null)
            {
                leftPanel.style.display = DisplayStyle.None;
                leftPanel.style.flexGrow = 0; // Reset it when hidden
            }
            if (centerView != null) centerView.style.display = DisplayStyle.Flex;
        }
    }

    private void OnBackClicked()
    {
        SetAppMode(true);

        foreach (GameObject box in _visualBoxes) Destroy(box);
        _visualBoxes.Clear();
        _itemObjects.Clear();

        foreach (var item in _inventory) SpawnVisualBox(item);
    }

    private void UpdateRightPanelState(bool isEnabled)
    {
        if (_inputLength != null) _inputLength.SetEnabled(isEnabled);
        if (_inputWidth != null) _inputWidth.SetEnabled(isEnabled);
        if (_inputHeight != null) _inputHeight.SetEnabled(isEnabled);
        if (_inputWeight != null) _inputWeight.SetEnabled(isEnabled);
        if (_inputGroup != null) _inputGroup.SetEnabled(isEnabled);
        if (_toggleStackable != null) _toggleStackable.SetEnabled(isEnabled);

        if (!isEnabled)
        {
            if (_inputLength != null) _inputLength.SetValueWithoutNotify(0);
            if (_inputWidth != null) _inputWidth.SetValueWithoutNotify(0);
            if (_inputHeight != null) _inputHeight.SetValueWithoutNotify(0);
            if (_inputWeight != null) _inputWeight.SetValueWithoutNotify(0);
            if (_inputGroup != null) _inputGroup.SetValueWithoutNotify("Standard");
            if (_toggleStackable != null) _toggleStackable.SetValueWithoutNotify(false);
        }
    }

    private void SetRightPanelToCreateMode()
    {
        if (_inputItemName != null) _inputItemName.SetValueWithoutNotify("");
        if (_inputLength != null) _inputLength.SetValueWithoutNotify(1f);
        if (_inputWidth != null) _inputWidth.SetValueWithoutNotify(1f);
        if (_inputHeight != null) _inputHeight.SetValueWithoutNotify(1f);
        if (_inputWeight != null) _inputWeight.SetValueWithoutNotify(1f);
        if (_toggleStackable != null) _toggleStackable.SetValueWithoutNotify(true);
        if (_inputGroup != null) _inputGroup.SetValueWithoutNotify("Standard");
        Update3DPreview();
    }

    private void Deselect3DBox()
    {
        int index = _inventory.IndexOf(_currentlySelectedItem);
        if (index >= 0 && index < _visualBoxes.Count)
        {
            SetBoxColor(_visualBoxes[index], _currentlySelectedItem.DisplayColor);

            // NEW: Turn it back into a brick when deselected
            Rigidbody rb = _visualBoxes[index].GetComponent<Rigidbody>();
            if (rb != null) rb.isKinematic = true;
        }
    }

    private void Update3DPreview()
    {
        if (_previewBox3D != null && previewSpawnPoint != null)
        {
            float l = _inputLength != null ? _inputLength.value : 1f;
            float w = _inputWidth != null ? _inputWidth.value : 1f;
            float h = _inputHeight != null ? _inputHeight.value : 1f;
            string group = _inputGroup != null ? _inputGroup.value : "Standard";

            _previewBox3D.transform.localScale = new Vector3(l, h, w);
            SetBoxColor(_previewBox3D, CargoItem.GetColorForGroup(group));
            _previewBox3D.transform.position = previewSpawnPoint.position + new Vector3(0, h / 2f, 0);
        }
    }

    private void Update()
    {
        if (_previewBox3D != null && _previewBox3D.activeInHierarchy)
        {
            _previewBox3D.transform.Rotate(Vector3.up * 45f * Time.deltaTime, Space.World);
        }
    }
    private void SetBoxColor(GameObject box, Color color)
    {
        if (box != null)
        {
            box.GetComponent<Renderer>().material.color = color;
        }
    }
    // --- NATIVE WINDOWS FILE EXPLORER HOOKS ---
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    public class OpenFileName
    {
        public int structSize = 0;
        public System.IntPtr hwndOwner = System.IntPtr.Zero;
        public System.IntPtr hInstance = System.IntPtr.Zero;
        public string filter = null;
        public string customFilter = null;
        public int maxCustFilter = 0;
        public int filterIndex = 0;
        public string file = null;
        public int maxFile = 0;
        public string fileTitle = null;
        public int maxFileTitle = 0;
        public string initialDir = null;
        public string title = null;
        public int flags = 0;
        public short fileOffset = 0;
        public short fileExtension = 0;
        public string defExt = null;
        public System.IntPtr custData = System.IntPtr.Zero;
        public System.IntPtr hook = System.IntPtr.Zero;
        public string templateName = null;
        public System.IntPtr reservedPtr = System.IntPtr.Zero;
        public int reservedInt = 0;
        public int flagsEx = 0;
    }

    [DllImport("Comdlg32.dll", SetLastError = true, ThrowOnUnmappableChar = true, CharSet = CharSet.Auto)]
    public static extern bool GetOpenFileName([In, Out] OpenFileName ofn);

    [DllImport("Comdlg32.dll", SetLastError = true, ThrowOnUnmappableChar = true, CharSet = CharSet.Auto)]
    public static extern bool GetSaveFileName([In, Out] OpenFileName ofn);
}