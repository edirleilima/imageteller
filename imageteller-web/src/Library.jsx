import React, { useEffect, useState } from 'react';
import { Container, Table, CircularProgress, Typography, Box, IconButton, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Button, Snackbar } from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import {Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import { getUserId } from './utils';
import { getStories, deleteStory } from './api';
import { useLocation } from 'react-router-dom';

const LibraryPage = () => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [selectedStoryId, setSelectedStoryId] = useState(null);
  
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const admin = queryParams.get('admin');

  const userCookie = getUserId();

  useEffect(() => {
    const fetchStories = async () => {
      setLoading(true);
      try {
        const data = await getStories(admin || userCookie);
        setStories(data);
      } catch (err) {
        setError('Failed to fetch stories.');
      }
      setLoading(false);
    };

    fetchStories();
  }, [admin, userCookie]);

  const handleClickOpenDialog = (storyId) => {
    setSelectedStoryId(storyId);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedStoryId(null);
  };

  const handleDeleteStory = async () => {
    try {
      const data = await deleteStory(selectedStoryId, userCookie);

      if (data.status === 'success') {
        setStories(stories.filter(story => story.id !== selectedStoryId));
        setOpenSnackbar(true);
      } else {
        console.error('Failed to delete story');
      }
    } catch (err) {
      console.error('Failed to delete story:', err);
    }
    handleCloseDialog();
  };

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };


  if (loading) {
    return <Box className="d-flex justify-content-center mt-4"><CircularProgress /></Box>;
  }

  if (error) {
    return <Typography className="mt-4" color="error">{error}</Typography>;
  }

  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', options);
  };

  return (
    <Container className="container p-5">
      <Typography className="h4 pb-4 text-center" variant="h4">
        User Library
      </Typography>      
      <Table className="table table-striped">
        <thead>
          <tr>
            <th>Title</th>
            <th>Date</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {stories.map((story, index) => (
            <tr>
              <td><Link to={`/story/${story.id}${admin ? `?admin=${admin}` : ''}`}>{story.title}</Link></td>              
              <td>{formatDate(story.date)}</td>
              <td>
                {story.can_delete === 1 && (
                  <IconButton color="secondary" onClick={() => handleClickOpenDialog(story.id)}>
                    <DeleteIcon />
                  </IconButton>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
      <Box className="d-flex justify-content-center mt-5">
        <Link to={`/`}>
          Create New Story
        </Link>
      </Box>

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Delete Confirmation</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this story?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteStory} color="secondary">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={openSnackbar}
        autoHideDuration={7000}
        onClose={handleCloseSnackbar}
        message="Story successfully deleted"
      />
    </Container>
  );
};

export default LibraryPage;
