from vtl_core.domain import models

box = models.Item("B-01", "Edison Trunk", 12345, "", 1, 2, 3, 315.0, True)
truck = models.Container("T-01", "Mario's", 60.0, 1200.0, 82.5, 5000)

def main():

    print("Box: ", box)
    print("Truck: ", truck)

    print("Box Vol: ", box.volume())
    print("Box Foot: ", box.footprint())
    print("Truck Vol: ", truck.volume())
    
    box.rotate('x')
    print("Box Foot: ", box.footprint())
    box.rotate('y')
    print("Box Foot: ", box.footprint())
    box.rotate('z')
    print("Box Foot: ", box.footprint())
    #box.rotate('a')
    #print("Box Foot: ", box.footprint())
    
    return

if __name__ == "__main__":
    main()