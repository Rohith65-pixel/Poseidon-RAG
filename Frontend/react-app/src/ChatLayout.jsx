import { useState } from "react";
import axios from 'axios';
import { Container, Row, Col, Card, Form, Button, Spinner, Badge } from 'react-bootstrap';
function ChatLayout() {
    const [input,setInput] = useState('');
    const [messages,setMessages] = useState([{ 
        role: 'ai',
        text: 'Hello! I am your Argo Ocean Assistant. Ask me about float locations, temperatures, or salinity!' 
        }]);
    const [isLoading,setLoading] = useState(false);

    const sendMessage = async (e) => {
        e.preventDefault();
        if(!input.trim()) return;

        const new_msg = {role: 'user', text: input};
        setMessages((prev) => [...prev, new_msg]);
        setInput('');
        setLoading(true);

        try {
            const res = await axios.post('http://localhost:8000/api/agent',
              {
                message: new_msg.text
              });
            setMessages((prev) => [...prev, { role: 'ai', text: res.data.response }]);
        }
        catch(error) {
            console.error("Deep Error Details:", error.response?.data);
            setMessages((prev) => [...prev, { role: 'error', text: 'Failed to reach the backend.' }]);
        } finally {
            setLoading(false); 
        }
    };

    return (
    <Container fluid className="p-3 vh-100 bg-light">
      <Row className="h-100">
        
        {/* LEFT COLUMN: The AI Chat Interface */}
        <Col md={5} className="d-flex flex-column h-100">
          <Card className="flex-grow-1 shadow-sm border-0">
            <Card.Header className="bg-primary text-white d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Argo Ocean Assistant</h5>
              <Badge bg="info">RAG + SQL Agent</Badge>
            </Card.Header>
            
            {/* Chat History Area */}
            <Card.Body className="overflow-auto" style={{ maxHeight: '75vh' }}>
              {messages.length === 0 ? (
                <p className="text-muted text-center mt-5">
                  Ask me about the Argo float data in the Indian Ocean!
                </p>
              ) : (
                messages.map((msg, index) => (
                  <div 
                    key={index} 
                    className={`mb-3 p-3 rounded ${
                      msg.role === 'user' ? 'bg-light text-dark ms-auto w-75 border' 
                      : msg.role === 'error' ? 'bg-danger text-white' 
                      : 'bg-primary bg-opacity-10 text-dark w-85'
                    }`}
                  >
                    <strong>{msg.role === 'user' ? 'You' : 'ArgoBot'}: </strong>
                    <span style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</span>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="text-center text-primary mt-3">
                  <Spinner animation="border" size="sm" /> <span>Analyzing Database...</span>
                </div>
              )}
            </Card.Body>

            {/* Input Form Area */}
            <Card.Footer className="bg-white border-0">
              <Form onSubmit={sendMessage} className="d-flex gap-2">
                <Form.Control
                  type="text"
                  placeholder="e.g., Find the float inside the Arabian Sea..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={isLoading}
                />
                <Button variant="primary" type="submit" disabled={isLoading}>
                  Send
                </Button>
              </Form>
            </Card.Footer>
          </Card>
        </Col>

        {/* RIGHT COLUMN: Map & Data Visualization Placeholder */}
        <Col md={7} className="h-100">
          <Card className="h-100 shadow-sm border-0 bg-white d-flex align-items-center justify-content-center">
            <div className="text-center text-muted">
              <h3>🗺️ Geospatial Map Area</h3>
              <p>We will integrate React-Leaflet or Plotly here next!</p>
            </div>
          </Card>
        </Col>

      </Row>
    </Container>
  );
}

export default ChatLayout;