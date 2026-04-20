using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class CargoItem
{
    public string Id; // Teammate's API uses this to track specific boxes
    public string Name;
    public float Length;
    public float Width;
    public float Height;
    public float Weight;
    public bool IsStackable;

    public string GroupName;
    public Color DisplayColor;

    // FIX: Capitalized to match your teammate's code exactly!
    public Vector3 Position;
    public Quaternion Rotation;

    // Constructor
    public CargoItem(string name, float l, float w, float h, float weight, bool stackable, string groupName)
    {
        Id = System.Guid.NewGuid().ToString(); // Generate a random unique ID for the API
        Name = name;
        Length = l;
        Width = w;
        Height = h;
        Weight = weight;
        IsStackable = stackable;
        GroupName = groupName;

        DisplayColor = GetColorForGroup(groupName);
    }

    // Helper function for colors
    public static Color GetColorForGroup(string group)
    {
        switch (group)
        {
            case "Standard": return new Color(0.6f, 0.4f, 0.2f); // Cardboard Brown
            case "Fragile": return new Color(0.2f, 0.6f, 1.0f);  // Light Blue
            case "Heavy": return new Color(0.8f, 0.2f, 0.2f);    // Red
            case "Electronics": return new Color(0.9f, 0.8f, 0.1f); // Yellow
            default: return Color.gray;
        }
    }
}

[System.Serializable]
public class InventoryData
{
    public float TruckLength;
    public float TruckWidth;
    public float TruckHeight;

    // API Settings
    public string AlgorithmPreference;
    public int MaxCalculationTime;

    public List<CargoItem> items;
}
[System.Serializable]
public class API_Truck
{
    public string id = "truck_01";
    public float width;   // Python expects 'width'
    public float height;  // Python expects 'height'
    public float depth;   // Python expects 'depth'
}

[System.Serializable]
public class API_Box
{
    public string id;
    public float width;
    public float height;
    public float depth;
    public float weight;
}

[System.Serializable]
public class API_PackingRequest
{
    public API_Truck truck;
    public List<API_Box> boxes;
}

[System.Serializable]
public class PackResponseItem
{
    public string id;
    public float x;
    public float y;
    public float z;
    public int rotation;
}

[System.Serializable]
public class PackResponseData
{
    public List<PackResponseItem> placed;
    public List<PackResponseItem> unplaced;
    public float utilization;
    public float runtime_ms;
    public List<string> notes;
}

[System.Serializable]
public class PackRequestItem
{
    public string Id;
    public float Length;
    public float Width;
    public float Height;
    public float Weight;
}

[System.Serializable]
public class PackRequestData
{
    public float TruckLength;
    public float TruckWidth;
    public float TruckHeight;
    public List<PackRequestItem> items;
}