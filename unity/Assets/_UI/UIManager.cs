using System.Collections.Generic; // Required for Lists
using UnityEngine;
using UnityEngine.UIElements;
using System.IO; // Required for writing files

[SerializeField] private PackingBackendClient backendClient;

public class UIManager : MonoBehaviour
{
    public static UIManager Instance;

    private void Awake()
    {
        Instance = this; // Set the instance when the game starts
    }
    [Header("Settings")]
    public VisualTreeAsset itemRowTemplate; // The UXML file we just made
    public GameObject boxPrefab;
    public Transform spawnLocation;

    [Header("Truck Settings")]
    public GameObject truckBedObject; // Drag your 'TruckBed' here in Inspector
    private FloatField _truckL, _truckW, _truckH;

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
    //private Dictionary<string, GameObject> _itemToBox = new Dictionary<string, GameObject>();
    private Dictionary<string, GameObject> _itemObjects = new Dictionary<string, GameObject>();

    private Button _btnSettings;
    private Button _btnCloseSettings;
    private VisualElement _settingsOverlay;

    private Label _lblWeight;
    private Label _lblVolume;
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
    // We store the Position (Vector3) and Rotation (Vector3) for each angle
    public Vector3 isoPos, isoRot;
    public Vector3 topPos, topRot;
    public Vector3 sidePos, sideRot;
    private int _currentViewIndex = 0;
    public CameraController cameraControl;

    // We can add weight/stackable later

    [Header("Truck Settings")]
    public GameObject truckFloorObject;  // The solid floor
    public GameObject truckVolumeObject; // The glass walls

    // The actual list of data
    private List<CargoItem> _inventory = new List<CargoItem>();

    public float TruckL => _truckL != null ? _truckL.value : 1f;
    public float TruckW => _truckW != null ? _truckW.value : 1f;
    public float TruckH => _truckH != null ? _truckH.value : 1f;

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
        _inputGroup = root.Q<DropdownField>("InputGroup");

        _btnGenerate = root.Q<Button>("BtnGenerate");
        _loadingOverlay = root.Q<VisualElement>("LoadingOverlay");
        if (_btnGenerate != null) _btnGenerate.clicked += OnGenerateClicked;

        _btnSettings = root.Q<Button>("BtnSettings");
        _btnCloseSettings = root.Q<Button>("BtnCloseSettings");
        _settingsOverlay = root.Q<VisualElement>("SettingsOverlay");

        _inputAlgorithm = root.Q<DropdownField>("InputAlgorithm");
        _inputTimeLimit = root.Q<SliderInt>("InputTimeLimit");

        // Listen for typing on all inputs (Using evt => bypasses the strict type error!)
        if (_inputItemName != null) _inputItemName.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputLength != null) _inputLength.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputWidth != null) _inputWidth.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputHeight != null) _inputHeight.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputWeight != null) _inputWeight.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_toggleStackable != null) _toggleStackable.RegisterValueChangedCallback(evt => OnInputChanged());
        if (_inputGroup != null) _inputGroup.RegisterValueChangedCallback(evt => OnInputChanged());

        // Set the panel to "Create Mode" when the app first opens
        SetRightPanelToCreateMode();

        _btnClearList = root.Q<Button>("BtnClearList");
        if (_btnClearList != null) _btnClearList.clicked += ClearAll;

        if (_btnSettings != null) _btnSettings.clicked += OpenSettings;
        if (_btnCloseSettings != null) _btnCloseSettings.clicked += CloseSettings;

        _btnBack = root.Q<Button>("BtnBack");
        if (_btnBack != null) _btnBack.clicked += OnBackClicked;

        // 1. Find the ListView
        _itemListView = root.Q<ListView>("ItemListView");

        // 2. Setup the List Logic (Crucial Step)
        ConfigureListView();

        if (_btnAdd != null)     _btnAdd.clicked += OnAddClicked;
        if (_btnSave != null)    _btnSave.clicked += OnSaveClicked;
        if (_btnLoad != null)    _btnLoad.clicked += OnLoadClicked;
        if (_btnFile != null)    _btnFile.clicked += OnFileClicked;
        if (_btnAddMenu != null) _btnAddMenu.clicked += OnAddMenuClicked;
        if (_btnView != null)    _btnView.clicked += OnViewClicked;
        if (_btnSort != null) _btnSort.clicked += OnSortClicked;

        _truckL.RegisterValueChangedCallback(evt => UpdateTruckSize());
        _truckW.RegisterValueChangedCallback(evt => UpdateTruckSize());
        _truckH.RegisterValueChangedCallback(evt => UpdateTruckSize());

        _itemListView.selectionChanged += OnItemSelected;

        SetAppMode(true); // Start in Inventory Mode
        UpdateRightPanelState(true);

        // --- DESELECTION FIX ---
        // Find the background panels
        var leftPanel = root.Q<VisualElement>("LeftPanel");
        var rightPanel = root.Q<VisualElement>("RightPanel");

        // Listen for clicks on the Left Panel
        if (leftPanel != null)
        {
            leftPanel.RegisterCallback<PointerDownEvent>(evt =>
            {
                // If they clicked the empty background or the empty part of the list
                var targetName = (evt.target as VisualElement)?.name;
                if (targetName == "LeftPanel" || targetName == "ItemListView")
                {
                    _itemListView.ClearSelection();
                }
            });
        }

        // Listen for clicks on the Right Panel
        if (rightPanel != null)
        {
            rightPanel.RegisterCallback<PointerDownEvent>(evt =>
            {
                // If they click the empty background of the right panel
                if ((evt.target as VisualElement)?.name == "RightPanel")
                {
                    _itemListView.ClearSelection();
                }
            });
        }

    }

    private void ConfigureListView()
    {
        // A. MAKE ITEM: Tell the list how to create a new visual row
        _itemListView.makeItem = () => itemRowTemplate.Instantiate();

        // B. BIND ITEM: Tell the list how to fill that row with data
        _itemListView.bindItem = (element, index) =>
        {
            var item = _inventory[index]; // Get the data

            // Search inside the 'ItemRow' template for the labels
            var nameLabel = element.Q<Label>("ItemName");
            var sizeLabel = element.Q<Label>("ItemSize");

            nameLabel.text = item.Name;
            sizeLabel.text = $"{item.Length} x {item.Width} x {item.Height}";

            var btnRemove = element.Q<Button>("BtnRemove");

            btnRemove.clicked -= () => RemoveItem(item);
            btnRemove.clicked += () => RemoveItem(item);

            // Optional: Change text color to match the box color?
            // nameLabel.style.color = item.DisplayColor;
        };

        // C. SOURCE: Tell the list where the data is coming from
        _itemListView.itemsSource = _inventory;
        _itemListView.fixedItemHeight = 40; // Match the height we set in UI Builder
    }

    private void OnAddClicked()
    {
        // 1. Grab values from the Right Panel
        float l = _inputLength.value;
        float w = _inputWidth.value;
        float h = _inputHeight.value;
        float weight = _inputWeight.value;
        bool isStackable = _toggleStackable.value;
        string group = _inputGroup != null ? _inputGroup.value : "Standard";

        // 2. PROPERLY GRAB THE CUSTOM NAME
        string itemName = $"Box {_inventory.Count + 1}"; // Default name
        if (_inputItemName != null && !string.IsNullOrWhiteSpace(_inputItemName.value))
        {
            itemName = _inputItemName.value; // Override with user's custom name!
        }

        // Safety check (Don't spawn invisible boxes)
        if (l <= 0 || w <= 0 || h <= 0) return;

        // 3. Create the NEW item with the correct name
        var newItem = new CargoItem(itemName, l, w, h, weight, isStackable, group);

        // 4. Add to list and 3D world
        _inventory.Add(newItem);
        SpawnVisualBox(newItem);

        // 5. THE AUTO-DESELECT FIX
        // Instantly clear the selection so the Right Panel resets to "1, 1, 1" for the next box!
        _itemListView.ClearSelection();
        SetRightPanelToCreateMode();

        // Refresh UI
        _itemListView.RefreshItems();
        UpdateMetrics();
    }

    private void SpawnVisualBox(CargoItem item)
    {
        // NEW: Spawn exactly in the middle of the truck, near the ceiling
        Vector3 safeSpawnPos = new Vector3(0, TruckH - (item.Height / 2f), 0);

        // Replace the old Instantiate line with this one:
        GameObject newBox = Instantiate(boxPrefab, safeSpawnPos, Quaternion.identity);

        newBox.transform.localScale = new Vector3(item.Length, item.Height, item.Width);
        newBox.GetComponent<Renderer>().material.color = item.DisplayColor;

        _visualBoxes.Add(newBox);
    }
    private void OnSaveClicked()
    {
        //Save current box positions back into inventory data
        foreach (CargoItem item in _inventory)
        {
            if(_itemObjects.TryGetValue(item.Id, out GameObject box) && box != null)
            {
                item.Position = box.transform.position;
                Debug.Log($"{item.Name} saved at position {item.Position}");
            }
        }

        // 1. Wrap the list
        InventoryData data = new InventoryData();
        data.items = _inventory;
        data.TruckLength = _truckL.value;
        data.TruckWidth = _truckW.value;
        data.TruckHeight = _truckH.value;
        data.AlgorithmPreference = _inputAlgorithm != null ? _inputAlgorithm.value : "Standard";
        data.MaxCalculationTime = _inputTimeLimit != null ? _inputTimeLimit.value : 10;

        // 2. Convert to JSON text
        string json = JsonUtility.ToJson(data, true); // 'true' makes it pretty/readable

        // 3. Define filename
        // Application.persistentDataPath is a safe folder on any OS
        string path = Path.Combine(Application.persistentDataPath, "loadout.json");

        // 4. Write to file
        File.WriteAllText(path, json);

        Debug.Log($"<color=cyan>SAVED JSON to:</color> {path}");
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
            rotatable = item.Stackable,
            priority = 0f
        });

        Debug.Log($"Pack item -> {item.Name} | id={item.Id} | W={item.Width} H={item.Height} D={item.Length} WT={item.Weight}");
    }

    return request;
}

    private void OnSortClicked()
    {
        PackingRequest request = BuildPackingRequest();
        StartCoroutine(backendClient.SendPackRequest(
            request,
            OnPackSuccess,
            OnPackError
        ));

        // WritePackRequestJSON();
        // WritePackResponseJSON();

    }
    private void ClearAll()
    {
        _itemListView.ClearSelection();
        // 1. Destroy all 3D objects
        foreach (GameObject box in _visualBoxes)
        {
            Destroy(box);
        }
        _visualBoxes.Clear();

        // 2. Clear the data list
        _inventory.Clear();
        _itemObjects.Clear();

        // 3. Update UI
        _itemListView.RefreshItems();

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
        foreach (var placed in response.placed)
        {
            if (_itemObjects.TryGetValue(placed.id, out GameObject box) && box != null)
            {
                Vector3 newPos = new Vector3(placed.x, placed.y, placed.z);
                box.transform.position = newPos;

                CargoItem item = _inventory.Find(i => i.Id == placed.id);
                if (item != null)
                    item.Position = newPos;

                Debug.Log($"Placed {placed.id} at {newPos}, rotation={placed.rotation}");
            }
            else
            {
                Debug.LogWarning($"No spawned box found for id {placed.id}");
            }
        }
    }

    if (response.unplaced != null)
    {
        foreach (var unplaced in response.unplaced)
        {
            Debug.LogWarning($"Unplaced box: {unplaced.id}");
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
        string path = Path.Combine(Application.persistentDataPath, "loadout.json");

        if (!File.Exists(path))
        {
            Debug.LogError("No save file found!");
            return;
        }

        // 1. Read the text
        string json = File.ReadAllText(path);

        // 2. Clear the current scene
        ClearAll();
        _itemObjects.Clear();

        // 3. Convert JSON back to Data
        InventoryData loadedData = JsonUtility.FromJson<InventoryData>(json);
        _truckL.value = loadedData.TruckLength;
        _truckW.value = loadedData.TruckWidth;
        _truckH.value = loadedData.TruckHeight;

        // 4. Re-populate everything
        foreach (CargoItem item in loadedData.items)
        {
            // Add to data list
            _inventory.Add(item);
            SpawnVisualBox(item);

            Debug.Log($"{item.Name} loaded at position {item.Position}");
        }

        // 5. Refresh UI
        _itemListView.RefreshItems();

        Debug.Log($"<color=green>LOADED:</color> {loadedData.items.Count} items.");
        UpdateMetrics();
    }
    private void UpdateTruckSize()
    {
        float l = _truckL.value;
        float w = _truckW.value;
        float h = _truckH.value; // Now we use H!

        if (l < 1) l = 1;
        if (w < 1) w = 1;
        if (h < 1) h = 1;

        // 1. Scale the Solid Floor (Always thin)
        truckFloorObject.transform.localScale = new Vector3(l, 0.1f, w);
        // Keep the floor at Y = 0
        truckFloorObject.transform.position = new Vector3(0, 0, 0);

        // 2. Scale the Glass Volume (Uses Height)
        if (truckVolumeObject != null)
        {
            truckVolumeObject.transform.localScale = new Vector3(l, h, w);

            // Unity scales from the center. If height is 10, it goes 5 up and 5 down.
            // We move it up by (Height / 2) so the bottom of the glass touches the floor.
            truckVolumeObject.transform.position = new Vector3(0, h / 2f, 0);
        }
    }
    private void RemoveItem(CargoItem itemToRemove)
    {
        // 1. Remove from Data List
        _inventory.Remove(itemToRemove);

        // 2. Remove the 3D visual associated with it
        // (This is tricky because our visual list matches the index of the data list)
        // To keep it simple for now, we will just Refresh the whole 3D scene:

        // Clear existing 3D boxes
        foreach (GameObject box in _visualBoxes) Destroy(box);
        _visualBoxes.Clear();

        // Respawn remaining items
        foreach (var item in _inventory) SpawnVisualBox(item);

        // 3. Refresh UI
        _itemListView.RefreshItems();

        Debug.Log($"Removed {itemToRemove.Name}");
        UpdateMetrics();
    }
    // 1. FILE BUTTON: Acts as "New Scene / Reset"
    private void OnFileClicked()
    {
        ClearAll(); // We already wrote this function!
        Debug.Log("Scene Reset (New File)");
    }

    // 2. ADD BUTTON: Acts as "Auto-Fill Random" (Great for testing)
    private void OnAddMenuClicked()
    {
        // Generate a random box size between 1 and 3
        float rL = Mathf.Round(Random.Range(1f, 3f) * 10f) / 10f; // Round to 1 decimal
        float rW = Mathf.Round(Random.Range(1f, 3f) * 10f) / 10f;
        float rH = Mathf.Round(Random.Range(1f, 3f) * 10f) / 10f;

        CargoItem randomItem = new CargoItem($"AutoBox {_inventory.Count + 1}", rL, rW, rH, 10, true, "Standard");

        _inventory.Add(randomItem);
        SpawnVisualBox(randomItem);
        _itemListView.RefreshItems();

        Debug.Log("Added Random Test Box");
    }

    // 3. VIEW BUTTON: Cycles Camera Angles
    private void OnViewClicked()
    {
        if (cameraControl == null) return;

        _currentViewIndex++;
        if (_currentViewIndex > 2) _currentViewIndex = 0;

        switch (_currentViewIndex)
        {
            case 0: // ISOMETRIC
                cameraControl.SetViewAngle(new Vector3(35, 45, 0)); // Standard Iso
                break;
            case 1: // TOP DOWN
                cameraControl.SetViewAngle(new Vector3(90, 0, 0));
                break;
            case 2: // SIDE VIEW
                cameraControl.SetViewAngle(new Vector3(0, -90, 0));
                break;
        }

        Debug.Log("Switched View Index: " + _currentViewIndex);
    }
    private void UpdateMetrics()
    {
        // 1. Calculate Truck Volume
        float truckL = _truckL.value;
        float truckW = _truckW.value;
        float truckH = _truckH.value;

        // Prevent dividing by zero if inputs are empty
        if (truckL <= 0 || truckW <= 0 || truckH <= 0) return;

        float maxVolume = truckL * truckW * truckH;

        // 2. Tally up the Boxes
        float currentVolume = 0f;
        float currentWeight = 0f;

        foreach (var item in _inventory)
        {
            currentVolume += (item.Length * item.Width * item.Height);
            currentWeight += item.Weight;
        }

        // 3. Calculate Percentage
        float fillPercentage = (currentVolume / maxVolume) * 100f;

        // 4. Update the UI Text (F1 formats it to 1 decimal place, e.g., "45.2")
        _lblWeight.text = $"Total Weight: {currentWeight:F1} kg";
        _lblVolume.text = $"Volume Used: {fillPercentage:F1}%";

        // Bonus: Make the text turn RED if you overfill the truck (>100%)
        if (fillPercentage > 100f)
            _lblVolume.style.color = Color.red;
        else
            _lblVolume.style.color = Color.white;
    }
    // This runs automatically whenever a row is clicked
    private void OnItemSelected(System.Collections.Generic.IEnumerable<object> selectedItems)
    {
        // 1. RESET COLORS: Turn all boxes back to their normal colors first
        for (int i = 0; i < _visualBoxes.Count; i++)
        {
            if (_visualBoxes[i] != null)
            {
                _visualBoxes[i].GetComponent<Renderer>().material.color = _inventory[i].DisplayColor;
            }
        }

        // 2. CHECK SELECTION: Did we actually click something?
        var enumerator = selectedItems.GetEnumerator();

        // IF THE USER DESELECTED (Clicked empty space)
        if (!enumerator.MoveNext())
        {
            _currentlySelectedItem = null;
            SetRightPanelToCreateMode(); // Snap back to Create Mode
            return;
        }

        // IF THE USER CLICKED A BOX
        CargoItem selectedData = (CargoItem)enumerator.Current;
        _currentlySelectedItem = selectedData;

        // Turn the 3D box Cyan
        int selectedIndex = _inventory.IndexOf(selectedData);
        if (selectedIndex >= 0 && selectedIndex < _visualBoxes.Count)
        {
            _visualBoxes[selectedIndex].GetComponent<Renderer>().material.color = Color.cyan;
        }

        // Push data to Right Panel WITHOUT triggering typing events
        if (_inputItemName != null) _inputItemName.SetValueWithoutNotify(selectedData.Name);
        _inputLength.SetValueWithoutNotify(selectedData.Length);
        _inputWidth.SetValueWithoutNotify(selectedData.Width);
        _inputHeight.SetValueWithoutNotify(selectedData.Height);
        _inputWeight.SetValueWithoutNotify(selectedData.Weight);
        _toggleStackable.SetValueWithoutNotify(selectedData.IsStackable);
        if (_inputGroup != null) _inputGroup.SetValueWithoutNotify(selectedData.GroupName);

        Debug.Log($"Selected {selectedData.Name} in the Editor!");
        UpdateRightPanelState(true);
    }

    private void OnInputChanged()
    {
        // 1. If we are in "Create Mode" (no box selected), do nothing. 
        if (_currentlySelectedItem == null) return;

        // 2. We are in "Edit Mode". Update the Data Object with the new numbers/text!
        if (_inputItemName != null) _currentlySelectedItem.Name = _inputItemName.value;
        _currentlySelectedItem.Length = _inputLength.value;
        _currentlySelectedItem.Width = _inputWidth.value;
        _currentlySelectedItem.Height = _inputHeight.value;
        _currentlySelectedItem.Weight = _inputWeight.value;
        _currentlySelectedItem.IsStackable = _toggleStackable.value;

        if (_inputGroup != null)
        {
            _currentlySelectedItem.GroupName = _inputGroup.value;
            _currentlySelectedItem.DisplayColor = CargoItem.GetColorForGroup(_inputGroup.value);
        }

        // 3. Find which 3D box this is
        int index = _inventory.IndexOf(_currentlySelectedItem);

        // 4. Update the 3D Box instantly!
        if (index >= 0 && index < _visualBoxes.Count)
        {
            GameObject boxToResize = _visualBoxes[index];
            boxToResize.transform.localScale = new Vector3(_currentlySelectedItem.Length, _currentlySelectedItem.Height, _currentlySelectedItem.Width);
            boxToResize.GetComponent<Renderer>().material.color = _currentlySelectedItem.DisplayColor;
        }

        // 5. Update the UI text in the Left Panel list and bottom metrics
        _itemListView.RefreshItems();
        UpdateMetrics();
    }
    public void SetSelectionFrom3D(GameObject clickedBox)
    {
        // Find which box this is in our visual list
        int index = _visualBoxes.IndexOf(clickedBox);
        if (index != -1)
        {
            // This physically selects the row in the Left Panel!
            // Which automatically triggers OnItemSelected and updates the Right Panel.
            _itemListView.SetSelection(index);
        }
    }

    public void ClearSelectionFrom3D()
    {
        _itemListView.ClearSelection();
    }
    private void OpenSettings()
    {
        _settingsOverlay.style.display = DisplayStyle.Flex;
    }

    private void CloseSettings()
    {
        _settingsOverlay.style.display = DisplayStyle.None;
    }
    private void OnGenerateClicked()
    {
        // Prevent clicking if there are no boxes
        if (_inventory.Count == 0)
        {
            Debug.LogWarning("Cannot generate: Truck is empty!");
            return;
        }

        // Start the fake waiting process
        StartCoroutine(MockAPICallRoutine());
    }

    private System.Collections.IEnumerator MockAPICallRoutine()
    {
        _loadingOverlay.style.display = DisplayStyle.Flex;

        // 1. Pretend we are sending the JSON to Python
        OnSaveClicked(); // This guarantees our JSON is updated before sending

        yield return new WaitForSeconds(3f);

        SetAppMode(false); // Switch to 3D Viewer Mode!

        _loadingOverlay.style.display = DisplayStyle.None;

        Debug.Log("Simulating Python Response (Coordinates Received!)...");

        // 2. FAKE RESULT PLACEMENT
        // We will place them in a neat diagonal line to prove we can control them via code
        float currentZ = 0f;
        float currentX = 0f;

        for (int i = 0; i < _visualBoxes.Count; i++)
        {
            GameObject box = _visualBoxes[i];
            CargoItem item = _inventory[i];

            // A. Turn off gravity so they don't fall over. 
            // In a finished loadout, boxes are static!
            Rigidbody rb = box.GetComponent<Rigidbody>();
            if (rb != null)
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
    }
    // True = Show List, False = Show 3D Truck
    public void SetAppMode(bool isInventoryMode)
    {
        var leftPanel = GetComponent<UIDocument>().rootVisualElement.Q<VisualElement>("LeftPanel");
        var centerView = GetComponent<UIDocument>().rootVisualElement.Q<VisualElement>("CenterView");

        if (isInventoryMode)
        {
            leftPanel.style.display = DisplayStyle.Flex; // Show List
            centerView.style.display = DisplayStyle.None; // Hide Truck View Container
        }
        else
        {
            leftPanel.style.display = DisplayStyle.None; // Hide List
            centerView.style.display = DisplayStyle.Flex; // Show Truck View Container

        }
    }
    private void OnBackClicked()
    {
        // 1. Switch back to Inventory Mode (Shows List, hides Center View)
        SetAppMode(true);

        // 2. Clean up the 3D scene (Remove the "Result" boxes)
        foreach (GameObject box in _visualBoxes) Destroy(box);
        _visualBoxes.Clear();

        // 3. Respawn the original inventory boxes so the user can edit them again
        foreach (var item in _inventory) SpawnVisualBox(item);

        Debug.Log("Returned to Editor Mode.");
    }
    private void UpdateRightPanelState(bool isEnabled)
    {
        // Enable/Disable the inputs
        _inputLength.SetEnabled(isEnabled);
        _inputWidth.SetEnabled(isEnabled);
        _inputHeight.SetEnabled(isEnabled);
        _inputWeight.SetEnabled(isEnabled);
        _inputGroup.SetEnabled(isEnabled);
        _toggleStackable.SetEnabled(isEnabled);

        // If disabled, clear the numbers so it looks "empty"
        if (!isEnabled)
        {
            _inputLength.SetValueWithoutNotify(0);
            _inputWidth.SetValueWithoutNotify(0);
            _inputHeight.SetValueWithoutNotify(0);
            _inputWeight.SetValueWithoutNotify(0);
            _inputGroup.SetValueWithoutNotify("Standard");
            _toggleStackable.SetValueWithoutNotify(false);
        }
    }
    private void SetRightPanelToCreateMode()
    {
        // Clear all inputs back to defaults WITHOUT triggering OnInputChanged
        if (_inputItemName != null) _inputItemName.SetValueWithoutNotify(""); 
        if (_inputLength != null) _inputLength.SetValueWithoutNotify(1f);
        if (_inputWidth != null) _inputWidth.SetValueWithoutNotify(1f);
        if (_inputHeight != null) _inputHeight.SetValueWithoutNotify(1f);
        if (_inputWeight != null) _inputWeight.SetValueWithoutNotify(1f);
        if (_toggleStackable != null) _toggleStackable.SetValueWithoutNotify(true);
        if (_inputGroup != null) _inputGroup.SetValueWithoutNotify("Standard");

    }
}