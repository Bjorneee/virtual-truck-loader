using UnityEngine;
using UnityEngine.EventSystems;

public class ObjectManipulator : MonoBehaviour
{
    public LayerMask boxLayer;
    private GameObject _selectedObject;
    private Rigidbody _selectedRb;
    private Vector3 _offset;
    private float _cameraDistance;

    void Update()
    {
        if (Camera.main == null || UIManager.Instance == null) return;

        // 1. SELECTION
        if (Input.GetMouseButtonDown(0))
        {
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject()) return;

            Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 100f, boxLayer))
            {
                _selectedObject = hit.transform.gameObject;
                _selectedRb = _selectedObject.GetComponent<Rigidbody>();

                // Track distance for smooth dragging
                _cameraDistance = Vector3.Distance(Camera.main.transform.position, _selectedObject.transform.position);
                _offset = _selectedObject.transform.position - GetMouseWorldPos();

                UIManager.Instance.SetSelectionFrom3D(_selectedObject);
            }
            else
            {
                _selectedObject = null;
                _selectedRb = null;
                UIManager.Instance.ClearSelectionFrom3D();
            }
        }

        // 2. PHYSICS-BASED DRAGGING
        if (_selectedObject != null && _selectedRb != null && Input.GetMouseButton(0))
        {
            Vector3 targetPos = GetMouseWorldPos() + _offset;

            // FENCE MATH (Stay inside truck)
            float halfTruckX = UIManager.Instance.TruckX / 2f;
            float halfTruckZ = UIManager.Instance.TruckZ / 2f;
            float halfBoxX = _selectedObject.transform.localScale.x / 2f;
            float halfBoxZ = _selectedObject.transform.localScale.z / 2f;

            targetPos.x = Mathf.Clamp(targetPos.x, -halfTruckX + halfBoxX, halfTruckX - halfBoxX);
            targetPos.z = Mathf.Clamp(targetPos.z, -halfTruckZ + halfBoxZ, halfTruckZ - halfBoxZ);

            // Force Y to stay at exactly half-height (keeps it on the floor)
            targetPos.y = _selectedObject.transform.localScale.y / 2f;

            // Prevent overlapping: do an overlap test at the desired target position.
            // Build local half extents from the object's current scale.
            Vector3 halfExtents = new Vector3(
                _selectedObject.transform.localScale.x / 2f,
                _selectedObject.transform.localScale.y / 2f,
                _selectedObject.transform.localScale.z / 2f
            );

            // Slightly shrink extents to allow tiny tolerance
            Vector3 testExtents = halfExtents - Vector3.one * 0.01f;
            if (testExtents.x < 0.01f) testExtents.x = 0.01f;
            if (testExtents.y < 0.01f) testExtents.y = 0.01f;
            if (testExtents.z < 0.01f) testExtents.z = 0.01f;

            // Use only boxLayer to detect other boxes
            int layerMask = boxLayer;

            Collider[] hits = Physics.OverlapBox(targetPos, testExtents, _selectedObject.transform.rotation, layerMask, QueryTriggerInteraction.Ignore);

            bool blocked = false;
            foreach (var col in hits)
            {
                if (col != null && col.gameObject != _selectedObject)
                {
                    blocked = true;
                    break;
                }
            }

            // If blocked, do not move into overlap. Otherwise move with physics to get collision responses.
            if (!blocked)
            {
                // Use MovePosition: This tells Unity "Move here, but stop if you hit something solid"
                _selectedRb.MovePosition(targetPos);
            }
        }
    }

    private Vector3 GetMouseWorldPos()
    {
        Vector3 mousePoint = Input.mousePosition;
        mousePoint.z = _cameraDistance;
        return Camera.main.ScreenToWorldPoint(mousePoint);
    }
}