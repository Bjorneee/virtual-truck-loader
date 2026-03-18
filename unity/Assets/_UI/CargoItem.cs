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
    public Color DisplayColor;

    public CargoItem(string name, float l, float w, float h, float weight, bool stackable)
    {
        Id = System.Guid.NewGuid().ToString();
        Name = name;
        Length = l;
        Width = w;
        Height = h;
        Weight = weight;
        IsStackable = stackable;

        Position = Vector3.zero;
        Rotation = Quaternion.identity;
        DisplayColor = Random.ColorHSV();
    }
}

[System.Serializable] 
public class InventoryData
{
    public float TruckLength;
    public float TruckWidth;
    public float TruckHeight;
    public List<CargoItem> items;
}