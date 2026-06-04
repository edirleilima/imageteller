import React, { useState } from 'react';
import { Container, Typography, Card, CardMedia, IconButton, CardContent, Box, Button, CircularProgress, TextField, MenuItem, ListSubheader } from '@mui/material';
import { Delete, Add } from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import Story from './Story';
import { getOrCreateUserId } from './utils';
import { generateStory, illustrateChapter, saveStory } from './api';
import { usePrintMode } from './usePrintMode';
import { Link, useNavigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';

const grid = 8;

const getItemStyle = (isDragging, draggableStyle) => ({
  userSelect: 'none',
  margin: `0 ${grid}px 0 0`,
  ...draggableStyle,
});

const getListStyle = (isDraggingOver) => ({
  display: 'flex',
  padding: grid,
  whiteSpace: 'nowrap',
  width: '100%',
});

const genreOptions = [
  { category: 'Story-Driven Genres', genres: ['Comedy', 'Romance', 'Tragedy', 'Satire', 'Mystery'] },
  { category: 'Data-Driven Genres', genres: ['Data Storytelling'] },
  { category: 'Player-Driven Genres', genres: ['Achiever', 'Explorer', 'Socializer', 'Killer'] },
];

function MainPage() {
  const [images, setImages] = useState([]);
  const [captions, setCaptions] = useState([]); 
  const [storyTitle, setStoryTitle] = useState('');
  const [storyId, setStoryId] = useState(0);
  const [userId, setUserId] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [composing, setComposing] = useState(false);
  const [selectedGenre, setSelectedGenre] = useState('Not Specified');
  const [chapters, setChapters] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [loadingChapters, setLoadingChapters] = useState(true);
  const [editButtonClass, setEditButtonClass] = useState('');


  const navigate = useNavigate();

  usePrintMode();

  const handleImageUpload = (event) => {
    const files = event.target.files;
    const newImages = Array.from(files).map((file) => ({
      url: URL.createObjectURL(file),
      name: file.name,
      type: file.type
    }));
    setImages((prevImages) => [...prevImages, ...newImages]);
    setCaptions((prevCaptions) => [...prevCaptions, ...new Array(files.length).fill('')]); 
  };

  const handleDeleteImage = (index) => {
    setImages((prevImages) => prevImages.filter((_, i) => i !== index));
    setCaptions((prevCaptions) => prevCaptions.filter((_, i) => i !== index)); 
  };

  const handleCaptionChange = (index, value) => {
    const newCaptions = [...captions];
    newCaptions[index] = value;
    setCaptions(newCaptions);
  };

  const handleOnDragEnd = (result) => {
    if (!result.destination) return;

    const items = Array.from(images);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    const newCaptions = Array.from(captions);
    const [reorderedCaption] = newCaptions.splice(result.source.index, 1);
    newCaptions.splice(result.destination.index, 0, reorderedCaption);

    setImages(items);
    setCaptions(newCaptions);
  };

  const handleGenerateStory = async () => {
    setLoading(true);
    setComposing(true);
    setStoryTitle('');
    setChapters([]);
    setErrorMessage('');

    const userid = getOrCreateUserId();
    setUserId(userid);

    const formData = new FormData();
    for (let i = 0; i < images.length; i++) {
      const image = images[i];
      const response = await fetch(image.url);
      const blob = await response.blob();
      formData.append('files', new File([blob], image.name, { type: image.type }));      
      formData.append('captions', captions[i]); 
    }

    try {
      const story = await generateStory(formData, selectedGenre, userid);
      setStoryTitle(story.title);
      setChapters(story.chapters);
      setStoryId(story.id);
      setLoading(false);
      
      await fetchChapterImages(story.chapters, story.id, userid);
    } catch (error) {
      console.error('Error generating story:', error);
      setErrorMessage('Failed to generate story. Please try again.'); 
      setLoading(false); 
      setComposing(false); 
    }

    
  };

  const fetchChapterImages = async (chapters, storyid, userid) => {
    for (let i = 0; i < chapters.length; i++) {      
      updateChapterImage(chapters[i].id, null);
    }
    for (let i = 0; i < chapters.length; i++) {      
      const chapter = chapters[i];
      updateChapterImage(chapter.id, null);
      try {
        const data = await illustrateChapter(storyid, chapter.id, chapter.text, userid);
        updateChapterImage(chapter.id, data.url + "?" + encodeURIComponent(new Date().toString()));                 
      } catch (error) {
        console.error(`Error fetching image for chapter ${chapter.title}:`, error);
      }
    }
    setLoadingChapters(false);
  };

  const handleNewStory = () => {
    setLoading(false);
    setComposing(false);
    setStoryTitle('');
    setChapters([]);
    setErrorMessage('');
  };

  const updateChapterImage = (chapterId, imageUrl) => {
    setChapters((prevChapters) =>
      prevChapters.map((chapter) =>
        chapter.id === chapterId ? { ...chapter, image: imageUrl } : chapter
      )
    );
  };

  const handleSaveStory = async () =>{
    setSaving(true);
    try {
      const data = await saveStory(storyId, userId);

      if (data.status === 'success') {
        
        navigate("/story/" + storyId);
      } else {
        console.error('Failed to save story');
        setErrorMessage('Failed to save story');
      }
    } catch (err) {
      console.error('Failed to save story:', err);
      setErrorMessage('Failed to save story: ' + err);
    }
    setSaving(false);
  };

  const handleGenreChange = (event) => {
    setSelectedGenre(event.target.value);
  };

  const menuItems = [
    <MenuItem key="Not Specified" value="Not Specified">
      Not Specified
    </MenuItem>,
    ...genreOptions.flatMap((categoryGroup) => [
      <ListSubheader
        key={categoryGroup.category}
        sx={{ backgroundColor: '#f0f0f0', fontWeight: 'bold', color: '#333' }}
      >
        {categoryGroup.category}
      </ListSubheader>,
      ...categoryGroup.genres.map((genre) => (
        <MenuItem key={genre} value={genre}>
          {genre}
        </MenuItem>
      )),
    ]),
  ];

  return (
    <Container className="container p-5">
      {loading && (
        <Box className="d-flex justify-content-center mt-4">
          <CircularProgress />
        </Box>
      )}
      {!composing && (
        <>
          <Typography className="h4 pb-4" variant="h4">
            ImageTeller - An AI-powered System that Creates Stories from Images
          </Typography>
          <Typography className="py-2" variant="body1">
            This system uses images to guide large language models in the process of generating stories.
          </Typography>
          <Typography className="py-2" variant="body1">
            To create a new story, please provide a sequence of images and select the genre of the story (optional).
          </Typography>
          <Typography component="div" className="py-2" variant="body1">
            <Box sx={{ fontWeight: 'bold' }}>Image Sequence:</Box>
          </Typography>
          <Box style={{ overflowX: 'auto' }}>
            <DragDropContext onDragEnd={handleOnDragEnd}>
              <Droppable droppableId="images" direction="horizontal">
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    style={getListStyle(snapshot.isDraggingOver)}
                    className="d-flex"
                  >
                    {images.map((image, index) => (
                      <Draggable key={index} draggableId={String(index)} index={index}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            style={getItemStyle(
                              snapshot.isDragging,
                              provided.draggableProps.style
                            )}
                            className="d-inline-block"
                          >
                            <Card sx={{ position: 'relative', width: 250 }}>
                              <CardMedia
                                component="img"
                                height="200"
                                image={image.url}
                                alt={`Story Event ${index + 1}`}
                              />
                              <CardContent>
                                <TextField
                                  fullWidth
                                  variant="outlined"
                                  placeholder="Optional caption"
                                  value={captions[index]}
                                  onChange={(e) => handleCaptionChange(index, e.target.value)}
                                />
                              </CardContent>
                              <IconButton
                                color="secondary"
                                aria-label="Delete Image"
                                onClick={() => handleDeleteImage(index)}
                                sx={{ position: 'absolute', top: 8, right: 8, backgroundColor: 'rgba(255, 255, 255, 0.7)' }}
                              >
                                <Delete />
                              </IconButton>
                            </Card>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                    <div style={{ width: 250, margin: `0 ${grid}px 0 0` }} className="d-inline-block">
                      <Card>
                        <CardContent
                          sx={{ height: 200, display: 'flex', justifyContent: 'center', alignItems: 'center' }}
                        >
                          <IconButton
                            color="primary"
                            aria-label="Upload Image"
                            component="label"
                          >
                            <input
                              type="file"
                              multiple
                              hidden
                              accept=".jpg, .jpeg, .png, .gif"
                              onChange={handleImageUpload}
                            />
                            <Add sx={{ fontSize: 60 }} />
                          </IconButton>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          </Box>
          <Typography component="div" className="py-2" variant="body1">
            <Box sx={{ fontWeight: 'bold' }}>Story Genre:</Box>
          </Typography>
          <Box className="d-flex overflow-auto">
            <TextField
              select
              value={selectedGenre}
              onChange={handleGenreChange}
              variant="outlined"
              sx={{ minWidth: 300, marginRight: 2 }}
            >
              {menuItems}
            </TextField>
          </Box>
          <Box className="d-flex justify-content-center mt-4">
            <Button variant="contained" color="primary" onClick={handleGenerateStory} disabled={loading}>
              {loading ? <CircularProgress size={24} /> : 'Generate Story'}
            </Button>
          </Box>
          {errorMessage && ( 
            <Box className="d-flex justify-content-center mt-4">
              <Typography color="error">{errorMessage}</Typography>
            </Box>
          )}
          <Box className="d-flex justify-content-center mt-4 pt-3">
            <Link to={`/library`}>
              View User Library
            </Link>
          </Box>
        </>
      )}
      {!loading && composing && (
        <Box>
            <Story 
                title={storyTitle} 
                chapters={chapters} 
                storyId={storyId} 
                userId={userId} 
                updateChapterImage={updateChapterImage} 
                updateChapters={setChapters} 
                loadingChapters={loadingChapters} 
                setLoadingChapters={setLoadingChapters}
                editButtonClass = {editButtonClass}
                setEditButtonClass = {setEditButtonClass}
            />
            <Box className="d-flex justify-content-center mt-2 mb-4">
                <Box className="d-flex justify-content-between" style={{ width: '100%', maxWidth: '400px' }}>
                    <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={handleSaveStory} 
                        style={{ flex: 1, marginRight: '10px' }}
                    >
                        {saving ? <CircularProgress size={24} /> : 'Save Story'}
                    </Button>
                    <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={handleNewStory} 
                        style={{ flex: 1 }}
                    >
                        Cancel and Return
                    </Button>
                </Box>
            </Box>
        </Box>
    
      )}
    </Container>
  );
}

export default MainPage;
