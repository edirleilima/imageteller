import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { List, ListItem, ListItemText, CircularProgress, Typography, Box } from '@mui/material';

const StoryList = ({ userId }) => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;

  useEffect(() => {
    const fetchStories = async () => {
      setLoading(true);
      try {
        const response = await axios.post(`${baseUrl}/get-stories/`, null, {
          params: {
            user: userId
          }
        });
        setStories(response.data);
      } catch (err) {
        setError('Failed to fetch stories.');
      }
      setLoading(false);
    };

    fetchStories();
  }, [userId]);

  if (loading) {
    return <Box className="d-flex justify-content-center mt-4"><CircularProgress /></Box>;
  }

  if (error) {
    return <Typography className="mt-4" color="error">{error}</Typography>;
  }

  return (
    <List>
      {stories.map((story) => (
        <ListItem key={story.id}>
          <ListItemText primary={story.title} />
        </ListItem>
      ))}
    </List>
  );
};

export default StoryList;
