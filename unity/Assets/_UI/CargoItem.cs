using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class CargoItem
{
    public string Name;
    public float Length;
    public float Width;
    public float Height;
    public float Weight;
    public bool IsStackable;
    public Color DisplayColor;

    public CargoItem(string name, float l, float w, float h, float weight, bool stackable)
    {
        Name = name;
        Length = l;
        Width = w;
        Height = h;
        Weight = weight;
        IsStackable = stackable;
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