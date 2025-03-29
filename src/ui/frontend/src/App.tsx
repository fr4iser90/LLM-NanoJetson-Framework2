import React, { useState, useEffect } from 'react';
import {
  ChakraProvider,
  Box,
  VStack,
  HStack,
  Text,
  Input,
  Button,
  Select,
  Progress,
  useToast,
  Card,
  CardBody,
  Heading,
  List,
  ListItem,
  Badge,
} from '@chakra-ui/react';

interface Task {
  id: string;
  type: string;
  status: string;
  description: string;
  progress: number;
  result?: any;
}

interface ProjectStatus {
  name: string;
  status: string;
  tasks: Task[];
  current_file?: string;
  progress: number;
}

function App() {
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [framework, setFramework] = useState('fastapi');
  const [status, setStatus] = useState<ProjectStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  // URLs für Browser-Zugriff
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:9999';
  const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:9999';

  useEffect(() => {
    if (status?.name) {
      console.log('Connecting to WebSocket:', `${WS_URL}/ws/projects/${status.name}/events`);
      const ws = new WebSocket(`${WS_URL}/ws/projects/${status.name}/events`);
      
      ws.onopen = () => console.log('WebSocket connected');
      ws.onclose = () => console.log('WebSocket closed');
      ws.onerror = (error) => console.error('WebSocket error:', error);
      
      ws.onmessage = (event) => {
        const newStatus = JSON.parse(event.data);
        setStatus(newStatus);
      };

      return () => {
        console.log('Closing WebSocket');
        ws.close();
      };
    }
  }, [status?.name, WS_URL]);

  const createProject = async () => {
    try {
      setIsLoading(true);
      // Nutze die konfigurierte API URL
      const response = await fetch(`${API_URL}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: projectName,
          description,
          framework,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create project');
      }

      const data = await response.json();
      setStatus(data);
      toast({
        title: 'Project Created',
        description: 'Starting development process...',
        status: 'success',
        duration: 5000,
      });
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChakraProvider>
      <Box p={8}>
        <VStack spacing={6} align="stretch">
          <Heading>AutoCoder Project Generator</Heading>

          {/* Project Creation Form */}
          <Card>
            <CardBody>
              <VStack spacing={4}>
                <Input
                  placeholder="Project Name"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
                <Input
                  placeholder="Project Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
                <Select
                  value={framework}
                  onChange={(e) => setFramework(e.target.value)}
                >
                  <option value="fastapi">FastAPI</option>
                  <option value="flask">Flask</option>
                  <option value="django">Django</option>
                  <option value="react">React</option>
                </Select>
                <Button
                  colorScheme="blue"
                  onClick={createProject}
                  isLoading={isLoading}
                  width="full"
                >
                  Create Project
                </Button>
              </VStack>
            </CardBody>
          </Card>

          {/* Project Status */}
          {status && (
            <Card>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <HStack justify="space-between">
                    <Heading size="md">{status.name}</Heading>
                    <Badge colorScheme={status.status === 'completed' ? 'green' : 'blue'}>
                      {status.status}
                    </Badge>
                  </HStack>
                  
                  <Progress value={status.progress * 100} />
                  
                  <List spacing={3}>
                    {status.tasks.map((task) => (
                      <ListItem key={task.id}>
                        <HStack justify="space-between">
                          <Text>{task.description}</Text>
                          <Badge colorScheme={
                            task.status === 'completed' ? 'green' :
                            task.status === 'running' ? 'blue' :
                            task.status === 'failed' ? 'red' : 'gray'
                          }>
                            {task.status}
                          </Badge>
                        </HStack>
                        {task.status === 'running' && (
                          <Progress size="sm" value={task.progress * 100} />
                        )}
                      </ListItem>
                    ))}
                  </List>
                </VStack>
              </CardBody>
            </Card>
          )}
        </VStack>
      </Box>
    </ChakraProvider>
  );
}

export default App; 