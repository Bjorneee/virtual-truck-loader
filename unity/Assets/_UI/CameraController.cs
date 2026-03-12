using UnityEngine;

public class CameraController : MonoBehaviour
{
    [Header("Settings")]
    public float moveSpeed = 10f;       // How fast WASD moves
    public float lookSensitivity = 2f;  // How fast mouse rotates
    public float scrollSpeed = 50f;     // Zoom speed

    private float _rotationX = 0f;
    private float _rotationY = 0f;

    void Start()
    {
        // Get the current rotation so we don't snap to 0,0 instantly
        Vector3 angles = transform.eulerAngles;
        _rotationX = angles.y;
        _rotationY = angles.x;
    }

    void Update()
    {
        // Only move if the Right Mouse Button is held down
        // This prevents the camera from moving while you are typing in the UI
        if (Input.GetMouseButton(1))
        {
            HandleRotation();
            HandleMovement();
        }

        HandleZoom();
    }

    void HandleRotation()
    {
        // 1. Get Mouse Input
        float mouseX = Input.GetAxis("Mouse X") * lookSensitivity;
        float mouseY = Input.GetAxis("Mouse Y") * lookSensitivity;

        // 2. Calculate new rotation
        _rotationX += mouseX;
        _rotationY -= mouseY;

        // Clamp looking up/down so you don't flip over
        _rotationY = Mathf.Clamp(_rotationY, -90f, 90f);

        // 3. Apply rotation
        transform.rotation = Quaternion.Euler(_rotationY, _rotationX, 0);
    }

    void HandleMovement()
    {
        float x = Input.GetAxis("Horizontal"); // A / D keys
        float z = Input.GetAxis("Vertical");   // W / S keys
        float y = 0;

        // Q and E to go Down/Up
        if (Input.GetKey(KeyCode.E)) y = 1;
        if (Input.GetKey(KeyCode.Q)) y = -1;

        Vector3 moveDir = (transform.right * x) + (transform.forward * z) + (transform.up * y);
        transform.position += moveDir * moveSpeed * Time.deltaTime;
    }

    void HandleZoom()
    {
        // Scroll wheel to zoom forward/backward
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        transform.position += transform.forward * scroll * scrollSpeed * Time.deltaTime;
    }
}