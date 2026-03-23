using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class CargoItem
{
    public string Id;
    public string Name;
    public float Length;
    public float Width;
    public float Height;
    public float Weight;
    public bool IsStackable;
    public Vector3 Position;
    public Quaternion Rotation;
    public string GroupName; // NEW: Track the category
    public Color DisplayColor;

    public CargoItem(string name, float l, float w, float h, float weight, bool stackable, string groupName)
    {
        Id = System.Guid.NewGuid().ToString();
        Name = name;
        Length = l;
        Width = w;
        Height = h;
        Weight = weight;
        IsStackable = stackable;
        GroupName = groupName;
        Position = Vector3.zero;
        Rotation = Quaternion.identity;

        // Assign color based on the group!
        DisplayColor = GetColorForGroup(groupName);
    }

    // Helper function to keep colors consistent
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
    // NEW: API Settings
    public string AlgorithmPreference;
    public int MaxCalculationTime;

    public List<CargoItem> items;
}