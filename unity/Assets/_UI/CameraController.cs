using UnityEngine;

public class CameraController : MonoBehaviour
{
    [Header("Target")]
    public Transform target; // Drag your 'TruckBed' here!

    [Header("Settings")]
    public float rotationSpeed = 5f;
    public float zoomSpeed = 10f;
    public float panSpeed = 0.5f;
    public float minZoom = 2f;
    public float maxZoom = 20f;

    private float _currentZoom = 10f;
    private Vector3 _currentRotation;
    private Vector3 _targetOffset; // For panning

    void Start()
    {
        // Initialize rotation based on current view
        _currentRotation = transform.eulerAngles;
        _currentZoom = Vector3.Distance(transform.position, target.position);
    }

    void Update()
    {
        if (target == null) return;

        // 1. ORBIT (Right Mouse Button)
        if (Input.GetMouseButton(1) && !Input.GetKey(KeyCode.LeftShift))
        {
            _currentRotation.x += Input.GetAxis("Mouse X") * rotationSpeed;
            _currentRotation.y -= Input.GetAxis("Mouse Y") * rotationSpeed;
            // Limit vertical angle so you don't go under the floor
            _currentRotation.y = Mathf.Clamp(_currentRotation.y, 5f, 85f);
        }

        // 2. PAN (Middle Mouse OR Shift + Right Click)
        if (Input.GetMouseButton(2) || (Input.GetMouseButton(1) && Input.GetKey(KeyCode.LeftShift)))
        {
            float x = Input.GetAxis("Mouse X") * panSpeed;
            float y = Input.GetAxis("Mouse Y") * panSpeed;

            // Move the focal point relative to camera facing
            _targetOffset -= transform.right * x;
            _targetOffset -= transform.up * y;
        }

        // 3. ZOOM (Scroll Wheel)
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        _currentZoom -= scroll * zoomSpeed;
        _currentZoom = Mathf.Clamp(_currentZoom, minZoom, maxZoom);

        // APPLY TRANSFORM
        // We calculate position based on: Target + Offset - (Rotation * Distance)
        Quaternion rotation = Quaternion.Euler(_currentRotation.y, _currentRotation.x, 0);
        Vector3 position = (target.position + _targetOffset) - (rotation * Vector3.forward * _currentZoom);

        if (position.y < 0.5f)
        {
            position.y = 0.5f;
        }

        transform.rotation = rotation;
        transform.position = position;
    }
    public void SetViewAngle(Vector3 newRotation)
    {
        _currentRotation = newRotation;

        // Optional: Reset zoom to default so you don't get lost
        _currentZoom = 15f;

        // Reset panning offset so you look straight at the truck
        _targetOffset = Vector3.zero;
    }
}