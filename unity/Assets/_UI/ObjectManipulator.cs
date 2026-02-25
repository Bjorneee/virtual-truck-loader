using UnityEngine;

public class ObjectManipulator : MonoBehaviour
{
    [Header("Settings")]
    public Material selectedMaterial; // The color when clicked (e.g., Bright Yellow)
    public LayerMask boxLayer; // To ensure we only click boxes, not the floor

    private GameObject _selectedObject;
    private Material _originalMaterial;
    private Vector3 _offset;
    private float _cameraDistance;

    void Update()
    {
        // 1. SELECTING (Left Click Down)
        if (Input.GetMouseButtonDown(0))
        {
            Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 100f, boxLayer))
            {
                SelectObject(hit.transform.gameObject);

                // Prepare for dragging
                _cameraDistance = hit.distance;
                _offset = hit.transform.position - GetMouseWorldPos();
            }
            else
            {
                // Clicked empty space? Deselect.
                DeselectObject();
            }
        }

        // 2. DRAGGING (Left Click Hold)
        if (_selectedObject != null && Input.GetMouseButton(0))
        {
            Vector3 targetPos = GetMouseWorldPos() + _offset;
            // Lock Y so it stays on the floor (optional, assumes floor is at Y=0 or box height)
            targetPos.y = _selectedObject.transform.position.y;

            _selectedObject.transform.position = targetPos;
        }

        // 3. DESELECT (Left Click Up)
        if (Input.GetMouseButtonUp(0))
        {
            // Optional: Snap to grid here if you want
        }
    }

    void SelectObject(GameObject obj)
    {
        if (_selectedObject == obj) return;

        DeselectObject(); // Reset previous

        _selectedObject = obj;
        var renderer = _selectedObject.GetComponent<Renderer>();
        _originalMaterial = renderer.material; // Remember original color
        renderer.material = selectedMaterial; // Change to highlight color
    }

    void DeselectObject()
    {
        if (_selectedObject != null)
        {
            _selectedObject.GetComponent<Renderer>().material = _originalMaterial; // Restore color
            _selectedObject = null;
        }
    }

    Vector3 GetMouseWorldPos()
    {
        Vector3 mousePoint = Input.mousePosition;
        mousePoint.z = _cameraDistance;
        return Camera.main.ScreenToWorldPoint(mousePoint);
    }
}