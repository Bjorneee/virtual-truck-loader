using UnityEngine;

/*
public class DragAndDrop3D : MonoBehaviour
{
    private Vector3 mousePositionOffset;

    
    void OnMouseDown()
    {
        // Calculate the offset between the object's position and the mouse position in screen space
        mousePositionOffset = gameObject.transform.position - GetMouseWorldPosition();
    }

    void OnMouseDrag()
    {
        // Update the object's position to follow the mouse while maintaining the original offset
        transform.position = GetMouseWorldPosition() + mousePositionOffset;
    }

    private Vector3 GetMouseWorldPosition()
    {
        // Convert screen space mouse position to world space position
        Vector3 mousePos = Input.mousePosition;
        // Ensure the z position is correct for a 3D environment perspective
        mousePos.z = Camera.main.WorldToScreenPoint(transform.position).z;
        return Camera.main.ScreenToWorldPoint(mousePos);
    }
}
*/

[RequireComponent(typeof(Collider))]
public class IsometricObjectDrag : MonoBehaviour
{
    public enum DragMode { FacePlane } // room for expansion later

    [Header("Dragging")]
    public LayerMask draggableMask = ~0;      // what can be selected
    public LayerMask snapTargetMask = ~0;     // what counts as "other boxes"
    public float hoverRayLength = 500f;

    [Header("Snapping")]
    public bool snapToTopOfBoxes = true;
    public bool snapXZToGrid = false;
    public Vector2 gridSizeXZ = new Vector2(2.5f, 2.5f);

    private Camera cam;
    private Plane dragPlane;
    private Vector3 dragOffset;               // world offset from hit point to object position
    private bool dragging;

    private Collider myCol;
    private float myHalfHeight;

    void Awake()
    {
        cam = Camera.main;
        myCol = GetComponent<Collider>();

        // If you use BoxCollider this is good; for other colliders, bounds works too.
        myHalfHeight = myCol.bounds.extents.y;
    }

    void OnMouseDown()
    {
        // Select only if we hit THIS object (prevents weird multi-object drags)
        Ray ray = cam.ScreenPointToRay(Input.mousePosition);
        if (!Physics.Raycast(ray, out RaycastHit hit, hoverRayLength, draggableMask))
            return;

        if (hit.collider != myCol)
            return;

        // Pick plane based on face normal (like editor-ish):
        // - If you clicked top/bottom face => move in XZ plane (ground plane)
        // - If you clicked a side face => move in a vertical plane
        Vector3 n = hit.normal;

        dragPlane = BuildPlaneFromFaceNormal(n, hit.point);

        // Compute offset so object doesn't "jump"
        if (dragPlane.Raycast(ray, out float enter))
        {
            Vector3 planePoint = ray.GetPoint(enter);
            dragOffset = transform.position - planePoint;
            dragging = true;
        }
    }

    void OnMouseDrag()
    {
        if (!dragging) return;

        Ray ray = cam.ScreenPointToRay(Input.mousePosition);

        if (!dragPlane.Raycast(ray, out float enter))
            return;

        Vector3 planePoint = ray.GetPoint(enter);
        Vector3 targetPos = planePoint + dragOffset;

        // Optional: snap XZ to grid while dragging
        if (snapXZToGrid)
        {
            targetPos.x = Mathf.Round(targetPos.x / gridSizeXZ.x) * gridSizeXZ.x;
            targetPos.z = Mathf.Round(targetPos.z / gridSizeXZ.y) * gridSizeXZ.y;
        }

        // Optional: stack-snap to top of other boxes if we're hovering one
        if (snapToTopOfBoxes && TryGetHoverSnap(ray, out Vector3 snapped))
        {
            // Keep X/Z from target, override Y from snapped
            targetPos.y = snapped.y;
        }

        transform.position = targetPos;
    }

    void OnMouseUp()
    {
        dragging = false;

        // Optional: final grid snap on release (if you want)
        if (snapXZToGrid)
        {
            var p = transform.position;
            p.x = Mathf.Round(p.x / gridSizeXZ.x) * gridSizeXZ.x;
            p.z = Mathf.Round(p.z / gridSizeXZ.y) * gridSizeXZ.y;
            transform.position = p;
        }
    }

    // Builds a drag plane based on which face was clicked
    private Plane BuildPlaneFromFaceNormal(Vector3 faceNormal, Vector3 hitPoint)
    {
        // Determine the dominant axis of the normal
        Vector3 abs = new Vector3(Mathf.Abs(faceNormal.x), Mathf.Abs(faceNormal.y), Mathf.Abs(faceNormal.z));

        // Clicked top/bottom: move on ground plane (XZ)
        if (abs.y >= abs.x && abs.y >= abs.z)
        {
            // Plane normal up => plane is XZ
            return new Plane(Vector3.up, hitPoint);
        }

        // Clicked left/right face: move on YZ plane (plane normal is X)
        if (abs.x >= abs.y && abs.x >= abs.z)
        {
            Vector3 planeNormal = Vector3.right; // plane perpendicular to X axis => YZ movement
            return new Plane(planeNormal, hitPoint);
        }

        // Clicked front/back face: move on XY plane (plane normal is Z)
        {
            Vector3 planeNormal = Vector3.forward; // plane perpendicular to Z axis => XY movement
            return new Plane(planeNormal, hitPoint);
        }
    }

    // Raycast to see if we're hovering another box; if so return the Y position to snap to its top
    private bool TryGetHoverSnap(Ray ray, out Vector3 snappedWorld)
    {
        snappedWorld = default;

        if (!Physics.Raycast(ray, out RaycastHit hit, hoverRayLength, snapTargetMask))
            return false;

        // Ignore self
        if (hit.collider == myCol)
            return false;

        // We only want to snap to "top" surfaces; simplest is bounds max.y.
        // Better would be: require hit.normal ~ Vector3.up, but in iso view you might hover sides.
        float otherTopY = hit.collider.bounds.max.y;

        // Put our object so its bottom sits on that top
        float newY = otherTopY + myHalfHeight;

        snappedWorld = new Vector3(transform.position.x, newY, transform.position.z);
        return true;
    }
}
