import { useState } from "react";
import axios from 'axios';
import { Container, Row, Col, Card, Form, Button, Spinner, Badge } from 'react-bootstrap';

import CsvLayout from "./CsvLayout";
import MapLayout from "./MapLayout";

function ChatLayout() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([{ 
        role: 'ai',
        text: 'Hello! I am your Argo Ocean Assistant. Ask me about float locations, temperatures, or salinity!' 
    }]);
    const [isLoading, setLoading] = useState(false);

    const sendMessage = async (e) => {
        e.preventDefault();
        if(!input.trim()) return;

        const new_msg = {role: 'user', text: input};
        setMessages((prev) => [...prev, new_msg]);
        setInput('');
        setLoading(true);

        try {
            const res = await axios.post('http://localhost:5000/api/agent', {
                message: new_msg.text
            });
            
            setMessages((prev) => [...prev, { role: 'ai', text: res.data.response,
                                              csv_data: res.data?.csv_data || [] ,
                                              points: res.data?.points || [] 
                                            }
                                  ]);
            
        } catch(error) {
            console.error("Deep Error Details:", error.response?.data);
            setMessages((prev) => [...prev, { role: 'error', text: 'Failed to reach the backend.' }]);
        } finally {
            setLoading(false); 
        }
    };

    return (
    <Container fluid className="p-3 vh-100 bg-light">
      <Row className="h-100">
        <Col className="d-flex flex-column h-100">
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
                    
                    <div className="mt-2 d-flex gap-2">
                      <br/>
                      {
                        msg.points?.length > 0 && 
                        <MapLayout mapPins={msg.points} />
                      }
                      {
                        msg.csv_data?.length > 0 && 
                        <CsvLayout csv_data={msg.csv_data} />
                      }
                    </div>
                    
                  </div>
                ))
              )}
              {isLoading && (
                <div className="text-center text-primary mt-3">
                  <Spinner animation="border" size="sm" /> <span className="ms-2">Analyzing Prompt....</span>
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
      </Row>
    </Container>
  );
}

export default ChatLayout;