using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;
using UnityEngine.UIElements;

using Debug = UnityEngine.Debug;

public enum MenuButtons
{
    File    = 0,
    Edit    = 1,
    View    = 2,
    Tools   = 3,
    Window  = 4,
    Help    = 5
}

public class MenuBarEvents : MonoBehaviour
{
    private UIDocument _document;

    private List<Button> _menuBarButtons;
    private List<Button> _dropDownButtons;

    private void Awake()
    {
        _document = GetComponent<UIDocument>();


        _menuBarButtons = _document.rootVisualElement.Query<Button>().ToList();
        for (int i = 0; i < _menuBarButtons.Count; i++)
        {
            _menuBarButtons[i].RegisterCallback<ClickEvent>(OnMenuBarButtonClicked);
        }

        foreach (var child in _menuBarButtons)
        {
            Debug.Log(child);
        }
    }

    private void OnDisable()
    {
        for (int i = 0; i < _menuBarButtons.Count; i++)
        {
            _menuBarButtons[i].RegisterCallback<ClickEvent>(OnMenuBarButtonClicked);
        }
    }

    private void OnMenuBarButtonClicked(ClickEvent e)
    {

    }

}
