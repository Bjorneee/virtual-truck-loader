using UnityEngine;
using UnityEngine.UIElements; // We need this to talk to the UI

public class UIManager : MonoBehaviour
{
    // This variable will hold the specific buttons and inputs
    private Button _btnAdd;
    private FloatField _inputLength;
    private FloatField _inputWidth;
    private FloatField _inputHeight;
    private FloatField _inputWeight;
    private Toggle _toggleStackable;

    // specialized Unity function that runs when the object turns on
    private void OnEnable()
    {
        // 1. Get the UI Document attached to this GameObject
        var uiDocument = GetComponent<UIDocument>();
        var root = uiDocument.rootVisualElement;

        // 2. Find the elements by the "Name" we gave them in UI Builder
        // "Q" stands for "Query" (Search)
        _btnAdd = root.Q<Button>("BtnAdd");

        _inputLength = root.Q<FloatField>("InputLength");
        _inputWidth = root.Q<FloatField>("InputWidth");
        _inputHeight = root.Q<FloatField>("InputHeight");
        _inputWeight = root.Q<FloatField>("InputWeight");

        _toggleStackable = root.Q<Toggle>("ToggleStackable");

        // 3. Add a "Listener" to the button
        // When clicked, run the function "OnAddClicked"
        if (_btnAdd != null)
        {
            _btnAdd.clicked += OnAddClicked;
        }
    }

    // The function that actually does the work
    private void OnAddClicked()
    {
        // Let's print the values to the Console to prove it works
        float l = _inputLength.value;
        float w = _inputWidth.value;
        float h = _inputHeight.value;
        bool isStackable = _toggleStackable.value;

        Debug.Log($"<color=green>SUCCESS:</color> Added Item! Size: {l}x{w}x{h}, Stackable: {isStackable}");
    }
}