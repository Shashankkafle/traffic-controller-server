import xml.etree.ElementTree as ET
import uuid
# automate the generation of this dict later
# needs to be updated for every scenario
# needs to be updated for every scenario
payload_to_node = {
"Way_IN_Table - Table":"N2TL",
"Way_Out_Table - Table":"TL2N",
"Traffic_Zone_Dashboard - Table":"N2TL",
}


def generate_possible_routes( edge_file):
    # Parse edge file
    tree = ET.parse(edge_file)
    root = tree.getroot()

    incoming = []
    outgoing = []

    for edge in root.findall('edge'):
        edge_id = edge.get('id')
        if edge_id.endswith('2TL'):
            incoming.append(edge_id)
        elif edge_id.startswith('TL2'):
            outgoing.append(edge_id)

    routes_root = ET.Element('routes')
    route_map = {}  # (from_dir, to_dir) -> route_id

    for inc in incoming:
        from_dir = inc  # e.g., 'N' from 'N2TL'
        for out in outgoing:
            to_dir = out  # e.g., 'S' from 'TL2S'
            if from_dir == to_dir:
                continue  # skip U-turns
            route_id = f"{from_dir}_{to_dir}"
            edges = f"{inc} {out}"
            ET.SubElement(routes_root, 'route', id=route_id, edges=edges)
            route_map[(from_dir, to_dir)] = route_id

    # Pretty-print and write
    ET.indent(routes_root, space="    ", level=0)
    tree = ET.ElementTree(routes_root)
   

    return route_map, tree


def vehicle_dict_from_api_data(api_data):
    vehicles_dict = {}
    
    for item in api_data:
        # can add checks for data validity here
        vehicle_id = item.get("License plate")
        # may have to change the checking condition based on ig we get none on missing values
        if not vehicle_id:
            # add a warning log here
            print("⚠️ Missing vehicle ID, skipping entry for id.",item.get("id"))
            continue
        current_entry = vehicles_dict.get(vehicle_id)
         # may need to handle case when the same vehicle crosses the intersection multiple times for now assuming that doesnot happen (entry and exit times may be sensitive to this case)
        entry_edge = payload_to_node.get(item.get("payload_name"), "UNKNOWN")

        if not current_entry:
            if entry_edge == "UNKNOWN":
                # add a warning log here
                print(f"⚠️ Unknown payload name {item.get('payload_name')} for vehicle {vehicle_id}, skipping entry.")
                continue
            vehicles_dict[vehicle_id] = {
                "Category": item.get("Category"),
                "Color": item.get("Color"),
                "Entry Timestamp": int(item.get("Trajectory start")), # Timestamp when the vehicle first appeared in the system
                "Trajectory start": item.get("Trajectory start"), #Value from DFS API refer to DFS docs for what it means
                "Trajectory end": item.get("Trajectory end"),  #Value from DFS API refer to DFS docs for what it means
                "Exit Timestamp": item.get("Trajectory end"),  # Timestamp when the vehicle last appeared in the system
                "Average speed": item.get("Average speed"),
                "Minimum speed": float(item.get("Minimum speed")),
                "Maximum speed": float(item.get("Maximum speed")),
                "Stationary duration": float(item.get("Stationary duration")),
                "payload_name": item.get("payload_name"),
                "entry_edge": entry_edge,
                "count": 1
            }
        else:
            exit_edge = "UNKNOWN"
            # may need to handle case where exit  node is already set and is different from current exit node
            if(current_entry["payload_name"] != item.get("payload_name")):
                # exit_edge = payload_to_node.get(item.get("payload_name"), "UNKNOWN")
                # only for testing purpose
                if entry_edge == "N2TL":
                    exit_edge = "TL2N"
                # exit_edge = payload_to_node.get(item.get("payload_name"), "UNKNOWN")
                if exit_edge == "UNKNOWN":
                    # add a warning log here
                       print(f"⚠️ Unknown payload name {item.get('payload_name')} for vehicle {vehicle_id}, skipping entry.")
                       continue
            current_entry["count"] += 1
            current_entry["exit_edge"] = exit_edge
            current_entry["Stationary duration"] += float(item.get("Stationary duration"))
            current_entry["Exit Timestamp"] = current_entry["Exit Timestamp"] if current_entry["Exit Timestamp"] >= item.get("Trajectory end") else item.get("Trajectory end")
            current_entry["Maximum speed"] = current_entry["Maximum speed"] if current_entry["Maximum speed"] >= float(item.get("Maximum speed")) else float(item.get("Maximum speed"))
            current_entry["Minimum speed"] = current_entry["Minimum speed"] if current_entry["Minimum speed"] <= float(item.get("Minimum speed")) else float(item.get("Minimum speed"))
            # current_entry["Average speed"] = (current_entry["Average speed"] * (current_entry["count"] -1) + item.get("Average speed")) / current_entry["count"]  # too complicated to calculate, skipping for now(may not be relevant for the simulation)  
    return vehicles_dict


def get_route_id(route_map, from_dir, to_dir):
    """Return the route id for given from/to directions."""
    return route_map.get((from_dir, to_dir), None)



def data_to_route(api_data,network_folder):
    """ function that creates a SUMO route file from the DFS API data"""
    vehicle_dict = vehicle_dict_from_api_data(api_data)
    sorted_vehicles = sorted(
    vehicle_dict.items(),
    key=lambda x: x[1]["Entry Timestamp"]
    )
    if sorted_vehicles:
        min_depart = sorted_vehicles[0][1]["Entry Timestamp"]
    else:
        print("⚠️ No vehicles found, skipping XML generation.")
        return
    route_map, route_tree = generate_possible_routes(f"{network_folder}/environment.edg.xml")
    print("route_map",route_map)
    # defiine multiple vehicle types later
    ET.SubElement(route_tree.getroot(), "vType", id="car", accel="2.6", decel="4.5", sigma="0.5", length="5", minGap="2.5", maxSpeed="50")
    ET.SubElement(route_tree.getroot(), "vType", id="motorcycle", accel="2.6", decel="4.5", sigma="0.5", length="5", minGap="2.5", maxSpeed="50")
    ET.SubElement(route_tree.getroot(), "vType", id="truck", accel="2.6", decel="4.5", sigma="0.5", length="5", minGap="2.5", maxSpeed="50")
    for key,vehicle in sorted_vehicles:
        from_edge = vehicle["entry_edge"]  # e.g. 'N2TL'
        to_edge  = vehicle["exit_edge"]  # e.g. 'TL2S'
        normalized_depart = vehicle["Entry Timestamp"] - min_depart
        route = route_map.get((from_edge, to_edge), None)
        # warning log here
        if(not route):
            print(f"⚠️ No route found for vehicle {key} from {from_edge} to {to_edge}, skipping vehicle.")
            continue
        # print("vehicle['Maximum speed']",vehicle["Maximum speed"] )
        # the magic umber 0.278 is to convert km/h to m/s
        # Maximim speed is not making sense with the current data double check before implementation
        ET.SubElement(route_tree.getroot(), "vehicle", id=key, depart=str(normalized_depart), departLane="random", departSpeed="10",maxSpeed = str(vehicle["Maximum speed"]/0.2778), type=vehicle["Category"], route=route)
    route_tree.write(f"{network_folder}/api.net.xml", encoding="UTF-8", xml_declaration=True)
    

    