import { useState } from "react";
import { Button, Modal } from "react-bootstrap";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { useMap } from "react-leaflet";
import { useEffect } from "react";

function MapLayout({ mapPins = [] }) {
  const [show, setShow] = useState(false);
  
  function ResizeMap() {
    const map = useMap();

    useEffect(() => {
      if (show) {
        setTimeout(() => {
          map.invalidateSize();
        }, 100);
      }
    }, [show, map]);

    return null;
  }

  return (
    <>
      <Button size="sm" onClick={() => setShow(true)} disabled={mapPins.length === 0}>
        Show Coordinates
      </Button>

      <Modal
        show={show}
        onHide={() => setShow(false)}
        size="xl"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Argo Float Locations</Modal.Title>
        </Modal.Header>

        <Modal.Body style={{ height: "70vh", padding: 0 }}>
          <MapContainer
            center={[15, 65]}
            zoom={4}
            style={{ height: "100%", width: "100%" }}
          >

            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution="&copy; OpenStreetMap contributors"
            />

            <ResizeMap />

            {mapPins.map((pin, index) => (
              <Marker
                key={index}
                position={[Number(pin.lat), Number(pin.lng)]}
              >
                <Popup>
                  <div className="text-center">
                    <strong>Platform ID:</strong> {pin.id}
                    <br />
                    <strong>Latitude:</strong>{" "}
                    {Number(pin.lat).toFixed(3)}°
                    <br />
                    <strong>Longitude:</strong>{" "}
                    {Number(pin.lng).toFixed(3)}°
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </Modal.Body>
      </Modal>
    </>
  );
}

export default MapLayout;