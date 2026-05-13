using UnityEngine;
using UnityEngine;
using UnityEngine.EventSystems;

public class ObjectManipulator : MonoBehaviour
{
    public LayerMask boxLayer;
    private GameObject _selectedObject;
    private Vector3 _grabPointOffset;

    void Update()
    {
        if (Camera.main == null || UIManager.Instance == null) return;

        // 1. SELECTION (Left Click Down)
        if (Input.GetMouseButtonDown(0))
        {
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject()) return;

            Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 100f, boxLayer))
            {
                _selectedObject = hit.transform.gameObject;

                // Calculate the offset so the box doesn't snap its center to the mouse
                _grabPointOffset = _selectedObject.transform.position - hit.point;

                UIManager.Instance.SetSelectionFrom3D(_selectedObject);
            }
            else
            {
                _selectedObject = null;
                UIManager.Instance.ClearSelectionFrom3D();
            }
        }

        // 2. PURE MATH DRAGGING
        if (_selectedObject != null && Input.GetMouseButton(0))
        {
            Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            Vector3 targetPos = _selectedObject.transform.position;

            // --- HOLD SHIFT TO MOVE UP AND DOWN ---
            if (Input.GetKey(KeyCode.LeftShift))
            {
                // Create a vertical plane facing the camera
                Plane vertPlane = new Plane(Camera.main.transform.forward, _selectedObject.transform.position);
                if (vertPlane.Raycast(ray, out float distance))
                {
                    targetPos.y = ray.GetPoint(distance).y + _grabPointOffset.y;
                }
            }
            // --- NORMAL MOVEMENT (SIDE TO SIDE) ---
            else
            {
                // Create a horizontal plane on the floor
                Plane horizPlane = new Plane(Vector3.up, _selectedObject.transform.position);
                if (horizPlane.Raycast(ray, out float distance))
                {
                    Vector3 hitPoint = ray.GetPoint(distance);
                    targetPos.x = hitPoint.x + _grabPointOffset.x;
                    targetPos.z = hitPoint.z + _grabPointOffset.z;
                }
            }

            // --- 3. THE INVISIBLE FENCE ---
            // Get the actual world-space extents from the collider (accounts for rotation)
            Collider boxCollider = _selectedObject.GetComponent<Collider>();
            float boxHalfX, boxHalfY, boxHalfZ;

            if (boxCollider != null)
            {
                boxHalfX = boxCollider.bounds.extents.x;
                boxHalfY = boxCollider.bounds.extents.y;
                boxHalfZ = boxCollider.bounds.extents.z;
                Debug.Log($"Using collider bounds - halfX: {boxHalfX}, halfY: {boxHalfY}, halfZ: {boxHalfZ}");
            }
            else
            {
                // Fallback to local scale if no collider
                boxHalfX = _selectedObject.transform.localScale.x / 2f;
                boxHalfY = _selectedObject.transform.localScale.y / 2f;
                boxHalfZ = _selectedObject.transform.localScale.z / 2f;
                Debug.Log($"Using localScale - halfX: {boxHalfX}, halfY: {boxHalfY}, halfZ: {boxHalfZ}");
            }

            // Force the target position to stay strictly inside the truck dimensions
            targetPos.x = Mathf.Clamp(targetPos.x, boxHalfX, UIManager.Instance.TruckL - boxHalfX);
            targetPos.y = Mathf.Clamp(targetPos.y, boxHalfY, UIManager.Instance.TruckH - boxHalfY);
            targetPos.z = Mathf.Clamp(targetPos.z, boxHalfZ, UIManager.Instance.TruckW - boxHalfZ);

            // --- 4. ANTI-OVERLAP SHIELD ---
            // Simply check if any other collider overlaps with our position
            // Disable our collider temporarily to avoid detecting ourselves
            Collider myCollider = _selectedObject.GetComponent<Collider>();
            if (myCollider != null) myCollider.enabled = false;

            // Use OverlapBox WITHOUT rotation - just check the axis-aligned box at target position
            // This is more accurate because we're checking the actual world-space extents
            Collider[] overlaps = Physics.OverlapBox(targetPos, new Vector3(boxHalfX * 0.99f, boxHalfY * 0.99f, boxHalfZ * 0.99f), Quaternion.identity, boxLayer);
            bool isBlocked = overlaps.Length > 0;

            if (isBlocked)
            {
                Debug.Log($"Blocked by {overlaps.Length} colliders at position {targetPos}");
            }

            // Turn our collider back on
            if (myCollider != null) myCollider.enabled = true;

            // Only move if the space is completely empty!
            if (!isBlocked)
            {
                _selectedObject.transform.position = targetPos;
            }
        }
    }
}