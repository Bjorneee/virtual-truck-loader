using System.Collections.Generic; // Required for Lists
using UnityEngine;
using UnityEngine.UIElements;
using System.IO; // Required for writing files

[SerializeField] private PackingBackendClient backendClient;

public class UIManager : MonoBehaviour
{
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
    private Button _btnSave;
    private List<GameObject> _visualBoxes = new List<GameObject>();
    private Button _btnLoad;
    private Button _btnFile;
    private Button _btnAddMenu;
    private Button _btnSort;
    private Button _btnView;
    //private Dictionary<string, GameObject> _itemToBox = new Dictionary<string, GameObject>();
    private Dictionary<string, GameObject> _itemObjects = new Dictionary<string, GameObject>();

    [Header("Camera Angles")]
    public Transform mainCamera;
    // We store the Position (Vector3) and Rotation (Vector3) for each angle
    public Vector3 isoPos, isoRot;
    public Vector3 topPos, topRot;
    public Vector3 sidePos, sideRot;
    private int _currentViewIndex = 0;
    // We can add weight/stackable later

    // The actual list of data
    private List<CargoItem> _inventory = new List<CargoItem>();

    private void OnEnable()
    {
        var root = GetComponent<UIDocument>().rootVisualElement;

        _btnAdd = root.Q<Button>("BtnAdd");
        _inputLength = root.Q<FloatField>("InputLength");
        _inputWidth = root.Q<FloatField>("InputWidth");
        _inputHeight = root.Q<FloatField>("InputHeight");
        _btnSave = root.Q<Button>("BtnSave");
        _btnLoad = root.Q<Button>("BtnLoad");
        _btnFile = root.Q<Button>("BtnFile");
        _btnAddMenu = root.Q<Button>("BtnAddMenu");
        _btnView = root.Q<Button>("BtnView");
        _btnSort = root.Q<Button>("BtnSort");

        _truckL = root.Q<FloatField>("TruckL");
        _truckW = root.Q<FloatField>("TruckW");
        _truckH = root.Q<FloatField>("TruckH");

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
        float l = _inputLength.value;
        float w = _inputWidth.value;
        float h = _inputHeight.value;

        if (l == 0 || w == 0 || h == 0) return;

        // 1. Create the Data Object
        var newItem = new CargoItem($"Box {_inventory.Count + 1}", l, w, h, 10, true);
        newItem.Position = spawnLocation.position;

        // 2. Add to our list
        _inventory.Add(newItem);

        // 3. Refresh the UI
        _itemListView.RefreshItems();

        // 4. (Still spawn visuals for fun/testing)
        SpawnVisualBox(newItem);
    }

    private void SpawnVisualBox(CargoItem item)
    {
        Vector3 spawnPos = item.Position != Vector3.zero ? item.Position : spawnLocation.position;
        //Vector3 spawnPos = item.Position;
        //if (spawnPos == Vector3.zero)
        //    spawnPos = spawnLocation.position;

        GameObject newBox = Instantiate(boxPrefab, spawnPos, Quaternion.identity);
        newBox.transform.localScale = new Vector3(item.Length, item.Height, item.Width);
        newBox.GetComponent<Renderer>().material.color = item.DisplayColor;

        _visualBoxes.Add(newBox);
        _itemObjects[item.Id] = newBox;//itemObjects or _itemToBox

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
    }
    private void UpdateTruckSize()
    {
        float l = _truckL.value;
        float w = _truckW.value;
        // Height doesn't change the floor visually, but saves for data

        if (l < 1) l = 1; // Prevent invisible trucks
        if (w < 1) w = 1;

        // Update the 3D Object
        // Note: Unity Plane scale 1 = 10 meters, Cube scale 1 = 1 meter.
        // Assuming your TruckBed is a Cube:
        truckBedObject.transform.localScale = new Vector3(l, 0.1f, w);
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

        CargoItem randomItem = new CargoItem($"AutoBox {_inventory.Count + 1}", rL, rW, rH, 10, true);

        _inventory.Add(randomItem);
        SpawnVisualBox(randomItem);
        _itemListView.RefreshItems();

        Debug.Log("Added Random Test Box");
    }

    // 3. VIEW BUTTON: Cycles Camera Angles
    private void OnViewClicked()
    {
        if (mainCamera == null) return;

        _currentViewIndex++;
        if (_currentViewIndex > 2) _currentViewIndex = 0;

        switch (_currentViewIndex)
        {
            case 0: // ISOMETRIC
                SetCamera(isoPos, isoRot);
                break;
            case 1: // TOP DOWN
                SetCamera(topPos, topRot);
                break;
            case 2: // SIDE VIEW
                SetCamera(sidePos, sideRot);
                break;
        }
    }

    private void SetCamera(Vector3 pos, Vector3 rot)
    {
        mainCamera.position = pos;
        mainCamera.rotation = Quaternion.Euler(rot);
    }
}