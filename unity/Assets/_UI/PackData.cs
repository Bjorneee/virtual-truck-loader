using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class PackRequestData
{
    public float TruckLength;
    public float TruckWidth;
    public float TruckHeight;
    public List<PackRequestItem> items;
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
public class PackResponseData
{
    public List<PackResponseItem> items;
}

[System.Serializable]
public class PackResponseItem
{
    public string Id;
    public Vector3 Position;
    public Quaternion Rotation;
}
