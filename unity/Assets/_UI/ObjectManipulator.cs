using UnityEngine;
using UnityEngine.EventSystems;

public class ObjectManipulator : MonoBehaviour
{
    public LayerMask boxLayer;

    private GameObject _selectedObject;
    private Vector3 _offset;
    private float _cameraDistance;

    void Update()
    {
        if (Camera.main == null) return;
        // 1. SELECTING (Left Click Down)
        if (Input.GetMouseButtonDown(0))
        {
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
            {
                return;
            }
            Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 100f, boxLayer))
            {
                _selectedObject = hit.transform.gameObject;

                // Prepare for dragging
                _cameraDistance = hit.distance;
                _offset = _selectedObject.transform.position - GetMouseWorldPos();

                // TELL THE UI WE CLICKED SOMETHING!
                if (UIManager.Instance != null)
                {
                    UIManager.Instance.SetSelectionFrom3D(_selectedObject);
                }
            }
            else
            {
                // Clicked empty space? Deselect.
                _selectedObject = null;
                if (UIManager.Instance != null)
                {
                    UIManager.Instance.ClearSelectionFrom3D();
                }
            }
        }
        // 2. DRAGGING (Left Click Hold)
        if (_selectedObject != null && Input.GetMouseButton(0))
        {
            Vector3 targetPos = GetMouseWorldPos() + _offset;

            // NEW: The "Invisible Fence"
            if (UIManager.Instance != null)
            {
                // Get the truck boundaries (divided by 2 because the truck is centered at 0,0)
                float maxL = UIManager.Instance.TruckL / 2f;
                float maxW = UIManager.Instance.TruckW / 2f;

                // Subtract half the box's size so the *edge* of the box doesn't hang off the floor
                float boxL = _selectedObject.transform.localScale.x / 2f;
                float boxW = _selectedObject.transform.localScale.z / 2f;

                // Clamp the X and Z coordinates so they cannot exceed the truck floor
                targetPos.x = Mathf.Clamp(targetPos.x, -maxL + boxL, maxL - boxL);
                targetPos.z = Mathf.Clamp(targetPos.z, -maxW + boxW, maxW - boxW);
            }

            float snapValue = 0.5f;
            targetPos.x = Mathf.Round(targetPos.x / snapValue) * snapValue;
            targetPos.z = Mathf.Round(targetPos.z / snapValue) * snapValue;

            targetPos.y = _selectedObject.transform.position.y;
            _selectedObject.transform.position = targetPos;
        }
        // Add this at the very end of your Update() function:
        // 4. THE SAFETY NET
        // If the box falls into the void due to physics knocking it over, teleport it back!
        if (_selectedObject != null && _selectedObject.transform.position.y < -2f)
        {
            _selectedObject.transform.position = new Vector3(0, UIManager.Instance.TruckH, 0);

            // Kill its momentum so it doesn't keep falling fast
            Rigidbody rb = _selectedObject.GetComponent<Rigidbody>();
            if (rb != null) rb.linearVelocity = Vector3.zero;
        }
    }

    Vector3 GetMouseWorldPos()
    {
        Vector3 mousePoint = Input.mousePosition;
        mousePoint.z = _cameraDistance;
        return Camera.main.ScreenToWorldPoint(mousePoint);
    }
}