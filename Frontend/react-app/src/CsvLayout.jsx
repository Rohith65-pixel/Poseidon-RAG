import { useState } from "react";
import { Modal, Button } from "react-bootstrap";
import { CSVLink } from "react-csv";

function CsvLayout({ csv_data = [] }) {
  const [show, setShow] = useState(false);

  const previewRows = csv_data.slice(0, 10);

  return (
    <>
      <Button
        size="sm"
        variant="primary"
        onClick={() => setShow(true)}
        disabled={csv_data.length === 0}
      >
        Show CSV Data
      </Button>

      <Modal
        show={show}
        onHide={() => setShow(false)}
        size="xl"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Query Results</Modal.Title>
        </Modal.Header>

        <Modal.Body className="overflow-auto">
          {csv_data.length > 0 ? (
            <>
              <div className="alert alert-info">
                Showing the first <strong>{previewRows.length}</strong> of{" "}
                <strong>{csv_data.length}</strong> rows.
                <br />
                Download the CSV below to view the complete results.
              </div>

              <div className="table-responsive">
                <table className="table table-striped table-bordered table-hover">
                  <thead className="table-dark">
                    <tr>
                      {Object.keys(previewRows[0]).map((key) => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {previewRows.map((row, index) => (
                      <tr key={index}>
                        {Object.values(row).map((value, i) => (
                          <td key={i}>{String(value)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p>No data available.</p>
          )}
        </Modal.Body>

        <Modal.Footer className="justify-content-between">
          <Button variant="secondary" onClick={() => setShow(false)}>
            Close
          </Button>

          {csv_data.length > 0 && (
            <CSVLink
              data={csv_data}
              filename="query_results.csv"
              className="btn btn-success"
            >
              Download All {csv_data.length} Rows
            </CSVLink>
          )}
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default CsvLayout;