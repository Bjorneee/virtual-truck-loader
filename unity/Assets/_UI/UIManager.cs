using System.Collections.Generic; // Required for Lists
using UnityEngine;
using UnityEngine.UIElements;
using System.IO; // Required for writing files

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
    private FloatField _inputWeight;
    private Toggle _toggleStackable;
    private Button _btnSave;
    private List<GameObject> _visualBoxes = new List<GameObject>();
    private Button _btnLoad;
    private Button _btnFile;
    private Button _btnAddMenu;
    private Button _btnView;
    private Label _lblWeight;
    private Label _lblVolume;
    private CargoItem _currentlySelectedItem = null;


    [Header("Camera Angles")]
    public Transform mainCamera;
    // We store the Position (Vector3) and Rotation (Vector3) for each angle
    public Vector3 isoPos, isoRot;
    public Vector3 topPos, topRot;
    public Vector3 sidePos, sideRot;
    private int _currentViewIndex = 0;
    public CameraController cameraControl;

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
        _inputWeight = root.Q<FloatField>("InputWeight");
        _toggleStackable = root.Q<Toggle>("ToggleStackable");
        _btnSave = root.Q<Button>("BtnSave");
        _btnLoad = root.Q<Button>("BtnLoad");
        _btnFile = root.Q<Button>("BtnFile");
        _btnAddMenu = root.Q<Button>("BtnAddMenu");
        _btnView = root.Q<Button>("BtnView");
        _truckL = root.Q<FloatField>("TruckL");
        _truckW = root.Q<FloatField>("TruckW");
        _truckH = root.Q<FloatField>("TruckH");
        _lblWeight = root.Q<Label>("LblWeight");
        _lblVolume = root.Q<Label>("LblVolume");

        _inputLength.RegisterValueChangedCallback(OnInputChanged);
        _inputWidth.RegisterValueChangedCallback(OnInputChanged);
        _inputHeight.RegisterValueChangedCallback(OnInputChanged);
        _inputWeight.RegisterValueChangedCallback(OnInputChanged);

        // 1. Find the ListView
        _itemListView = root.Q<ListView>("ItemListView");

        // 2. Setup the List Logic (Crucial Step)
        ConfigureListView();

        if (_btnAdd != null)
            _btnAdd.clicked += OnAddClicked;
        if (_btnSave != null)
            _btnSave.clicked += OnSaveClicked;
        if (_btnLoad != null)
            _btnLoad.clicked += OnLoadClicked;
        if (_btnFile != null) _btnFile.clicked += OnFileClicked;
        if (_btnAddMenu != null) _btnAddMenu.clicked += OnAddMenuClicked;
        if (_btnView != null) _btnView.clicked += OnViewClicked;

        _truckL.RegisterValueChangedCallback(evt => UpdateTruckSize());
        _truckW.RegisterValueChangedCallback(evt => UpdateTruckSize());
        _truckH.RegisterValueChangedCallback(evt => UpdateTruckSize());

        _itemListView.selectionChanged += OnItemSelected;


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
        _itemListView.ClearSelection();
        _currentlySelectedItem = null;
        float l = _inputLength.value;
        float w = _inputWidth.value;
        float h = _inputHeight.value;
        float weight = _inputWeight.value;
        bool isStackable = _toggleStackable.value;

        if (l == 0 || w == 0 || h == 0) return;

        var newItem = new CargoItem($"Box {_inventory.Count + 1}", l, w, h, weight, isStackable);

        _inventory.Add(newItem);
        _itemListView.RefreshItems();
        SpawnVisualBox(newItem);
        UpdateMetrics();
    }

    private void SpawnVisualBox(CargoItem item)
    {
        GameObject newBox = Instantiate(boxPrefab, spawnLocation.position, Quaternion.identity);
        newBox.transform.localScale = new Vector3(item.Length, item.Height, item.Width);
        newBox.GetComponent<Renderer>().material.color = item.DisplayColor;
        _visualBoxes.Add(newBox);

    }
    private void OnSaveClicked()
    {
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

        // 3. Update UI
        _itemListView.RefreshItems();
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

        // 2. Clear the current scene first!
        ClearAll();

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

            // Spawn visual (This will look cool as they all drop in!)
            SpawnVisualBox(item);
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
        // Height doesn't change the floor visually, but saves for data

        if (l < 1) l = 1; // Prevent invisible trucks
        if (w < 1) w = 1;

        // Update the 3D Object
        // Note: Unity Plane scale 1 = 10 meters, Cube scale 1 = 1 meter.
        // Assuming your TruckBed is a Cube:
        truckBedObject.transform.localScale = new Vector3(l, 0.1f, w);
        UpdateMetrics();
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

        CargoItem randomItem = new CargoItem($"AutoBox {_inventory.Count + 1}", rL, rW, rH, 10, true);

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
        if (!enumerator.MoveNext())
        {
            _currentlySelectedItem = null; // We deselected
            return;
        }

        // 3. GET THE DATA: Grab the specific CargoItem we clicked
        CargoItem selectedData = (CargoItem)enumerator.Current;
        _currentlySelectedItem = selectedData;

        // Find out which row number this is (Index)
        int selectedIndex = _inventory.IndexOf(selectedData);

        // 4. HIGHLIGHT 3D BOX: Turn the corresponding 3D box Bright Yellow
        if (selectedIndex >= 0 && selectedIndex < _visualBoxes.Count)
        {
            _visualBoxes[selectedIndex].GetComponent<Renderer>().material.color = Color.yellow;
        }

        // 5. FILL RIGHT PANEL: Push the data into the input fields
        _inputLength.value = selectedData.Length;
        _inputWidth.value = selectedData.Width;
        _inputHeight.value = selectedData.Height;
        _inputWeight.value = selectedData.Weight;
        _toggleStackable.value = selectedData.IsStackable;

        Debug.Log($"Selected {selectedData.Name} in the Editor!");
    }
    private void OnInputChanged(ChangeEvent<float> evt)
    {
        // If we haven't clicked a box in the list, don't do anything.
        // (This allows us to still type numbers to create NEW boxes)
        if (_currentlySelectedItem == null) return;

        // 1. Update the Data Object with the new numbers
        _currentlySelectedItem.Length = _inputLength.value;
        _currentlySelectedItem.Width = _inputWidth.value;
        _currentlySelectedItem.Height = _inputHeight.value;
        _currentlySelectedItem.Weight = _inputWeight.value;

        // 2. Find which 3D box this is
        int index = _inventory.IndexOf(_currentlySelectedItem);

        // 3. Resize the 3D Box instantly!
        if (index >= 0 && index < _visualBoxes.Count)
        {
            GameObject boxToResize = _visualBoxes[index];
            boxToResize.transform.localScale = new Vector3(
                _currentlySelectedItem.Length,
                _currentlySelectedItem.Height,
                _currentlySelectedItem.Width
            );
        }

        // 4. Update the UI text in the Left Panel list
        _itemListView.RefreshItems();

        // 5. Update the Total Volume/Weight calculations at the bottom left
        UpdateMetrics();
    }
}