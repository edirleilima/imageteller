import React, { useState } from 'react';
import { Container, Typography, Box, CircularProgress, IconButton, Tooltip,  Menu, MenuItem } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ReactMarkdown from 'react-markdown';
import { NestedMenuItem, IconMenuItem } from 'mui-nested-menu';
import EditIcon from '@mui/icons-material/Edit';
import ImageIcon from '@mui/icons-material/Image';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import DirectionsRunIcon from '@mui/icons-material/DirectionsRun';
import 'bootstrap/dist/css/bootstrap.min.css';
import './Story.css';
import axios from 'axios';

const placeholderImage = process.env.REACT_APP_PLACEHOLDER_IMAGE_URL;

const Story = ({ title, chapters, storyId, userId, updateChapterImage, updateChapters, loadingChapters, setLoadingChapters, editButtonClass, setEditButtonClass}) => {
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [regenerating, setRegenerating] = useState({});
  const open = Boolean(anchorEl);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;

  const handleReloadImage = async (chapter) => {
    handleEditClose();
    updateChapterImage(chapter.id, null); 
    try {
      const response = await axios.post(`${baseUrl}/illustrate-chapter/`, {
        story_id: storyId.toString(),
        chapter_id: chapter.id.toString(),
        text: chapter.text,
        user: userId
      }, {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      updateChapterImage(chapter.id, response.data.url + "?" + encodeURIComponent(new Date().toString()));
    } catch (error) {
      console.error(`Error regenerating image for chapter ${chapter.title}:`, error);
      updateChapterImage(chapter.id, placeholderImage); 
    }
  };

  const fetchChapterImages = async (chapters, storyid) => {

    const checkImageExists = async (url) => {
      try {
        const response = await fetch(url, { method: 'HEAD' });
        return response.status === 200;
      } catch (error) {
        return false;
      }
    };

    const updatedChapters = [...chapters];

    for (let i = 0; i < updatedChapters.length; i++) {
      updatedChapters[i].image = null;      
    }
    updateChapters([...updatedChapters]);

    for (let i = 0; i < updatedChapters.length; i++) {
      const chapter = updatedChapters[i];
      const imageUrl = `${baseUrl}/chapters/${storyid}/${chapter.id}`;

      const imageExists = await checkImageExists(imageUrl);

      if (!imageExists) {
        try {
          const response = await axios.post(`${baseUrl}/illustrate-chapter/`, {
            "story_id": storyid.toString(),
            "chapter_id": chapter.id.toString(),
            "text": chapter.text,
            "user": userId
          }, {
            headers: {
              'Content-Type': 'application/json',
            }
          });
          updatedChapters[i].image = response.data.url;
        } catch (error) {
          console.error(`Error generating image for chapter ${chapter.title}:`, error);
        }
      } else {
        updatedChapters[i].image = imageUrl;
      }

      updateChapters([...updatedChapters]); 
      
    } 
    setLoadingChapters(false);  
  };

  const handleRegenerateChapter = async (chapter) => {
    handleEditClose();
    setLoadingChapters(true);
    setRegenerating((prev) => {
      const newRegenerating = { ...prev };
      newRegenerating[chapter.id] = true;
      chapters.forEach((ch) => {
        if (ch.id > chapter.id) {
          newRegenerating[ch.id] = true;
        }
      });
      return newRegenerating;
    });
    try {
      const response = await axios.post(`${baseUrl}/regenerate-chapter/`, {
        story_id: storyId.toString(),
        chapter_id: chapter.id.toString(),
        text: "",
        user: userId
      }, {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      console.log(response.data);
      const story = response.data.story;
      setRegenerating((prev) => {
        const newRegenerating = { ...prev };
        newRegenerating[chapter.id] = false;
        chapters.forEach((ch) => {
          if (ch.id > chapter.id) {
            newRegenerating[ch.id] = false;
          }
        });
        return newRegenerating;
      });
      await fetchChapterImages(story.chapters, story.id);   
      
    } catch (error) {
      console.error(`Error regenerating image for chapter ${chapter.title}:`, error);
      setRegenerating((prev) => {
        const newRegenerating = { ...prev };
        newRegenerating[chapter.id] = false;
        chapters.forEach((ch) => {
          if (ch.id > chapter.id) {
            newRegenerating[ch.id] = false;
          }
        });
        return newRegenerating;
      });
      setLoadingChapters(false);
    }
  };

  const handleEditClick = (e, ch) => {
    setAnchorEl(e.currentTarget);
    setSelectedChapter(ch);
  }
  const handleEditClose = () => setAnchorEl(null);


  return (
    <Container className="container p-5">
      <Typography className="h3 pb-4 text-center mb-4" variant="h3">
        {title}
      </Typography>
      {chapters.map((chapter, index) => (
        <Box key={index} className={`mb-5`} sx={{ position: 'relative' }}>
          {regenerating[chapter.id] && ( 
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: 10,
              }}
            >
              <CircularProgress size={80} />
            </Box>
          )}
          <Box className="d-flex justify-content-between align-items-center">
            <Typography className="h4 pb-3" variant="h4">
              {chapter.title}
            </Typography>
            <Tooltip title="Edit Chapter" arrow>
              <IconButton
                variant="contained"
                onClick={(event) => handleEditClick(event, chapter)}
                className={editButtonClass}
                id={`chapteredit${chapter.id}`}
                disabled={loadingChapters}
              >
                <EditIcon fontSize="large" />
              </IconButton>
              <Menu anchorEl={anchorEl} open={open} onClose={handleEditClose}>
                <IconMenuItem
                  onClick={() => { handleReloadImage(selectedChapter); }}
                  leftIcon={<ImageIcon />}
                  label="Regenerate Illustration"
                />
                <IconMenuItem
                  onClick={() => { handleRegenerateChapter(selectedChapter); }}
                  leftIcon={<RefreshIcon />}
                  label="Regenerate Chapter"
                />
                <NestedMenuItem
                  label="Expand Chapter"
                  parentMenuOpen={open}
                  leftIcon={<UnfoldMoreIcon />}
                  className='d-none'
                >
                  <MenuItem onClick={handleEditClose} disabled>Add Descriptive Details</MenuItem>
                  <MenuItem onClick={handleEditClose} disabled>Add Dialogues</MenuItem>
                  <MenuItem onClick={handleEditClose} disabled>Add Internal Monologue</MenuItem>
                  <MenuItem onClick={handleEditClose} disabled>Add Character Backstory</MenuItem>
                  <MenuItem onClick={handleEditClose} disabled>Add Subplot</MenuItem>
                  <MenuItem onClick={handleEditClose} disabled>Add Foreshadowing</MenuItem>
                  <MenuItem onClick={handleEditClose} disabled>Add Flashback</MenuItem>
                </NestedMenuItem>
                <IconMenuItem
                  onClick={handleEditClose}
                  leftIcon={<UnfoldLessIcon />}
                  label="Summarize Chapter"
                  className='d-none'
                  disabled
                />
                <NestedMenuItem
                  label="Adjust Pace"
                  parentMenuOpen={open}
                  leftIcon={<DirectionsRunIcon />}
                  className='d-none'
                >
                  <MenuItem onClick={handleEditClose} disabled>Slow Down</MenuItem>
                  <MenuItem onClick={handleEditClose} disabled>Speed Up</MenuItem>
                </NestedMenuItem>
              </Menu>
            </Tooltip>
          </Box>
          <Box className="chapter-content d-flex" sx={{ position: 'relative' }}>
            {chapter.alignment === 'left' && (
              <Box className="mx-3" sx={{ width: '50%', height: '512px', position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Box sx={{ position: 'relative' }}>
                  <img src={chapter.image !== null ? chapter.image : placeholderImage} alt={`Illustration for ${chapter.title}`} style={{ maxWidth: '100%', maxHeight: '100%' }} />
                  {chapter.image === null && <CircularProgress sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }} />}
                  <Tooltip title="Regenerate Image" arrow>
                    <IconButton
                      sx={{ position: 'absolute', top: 2, right: 2, backgroundColor: 'rgba(255, 255, 255, 0.5)' }}
                      onClick={() => handleReloadImage(chapter)}
                      className='btreload d-none'
                      id={`img${chapter.id}`}
                    >
                      <RefreshIcon fontSize="large" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            )}
            <ReactMarkdown className="chapter-text" children={chapter.text} />
            {chapter.alignment === 'right' && (
              <Box className="mx-3" sx={{ width: '50%', height: '512px', position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Box sx={{ position: 'relative' }}>
                  <img src={chapter.image !== null ? chapter.image : placeholderImage} alt={`Illustration for ${chapter.title}`} style={{ maxWidth: '100%', maxHeight: '100%' }} />
                  {chapter.image === null && <CircularProgress sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }} />}
                  <Tooltip title="Regenerate Image" arrow>
                    <IconButton
                      sx={{ position: 'absolute', top: 2, right: 2, backgroundColor: 'rgba(255, 255, 255, 0.5)' }}
                      onClick={() => handleReloadImage(chapter)}
                      className='btreload d-none'
                      id={`img${chapter.id}`}
                    >
                      <RefreshIcon fontSize="large" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            )}
          </Box>
          {chapter.alignment === 'full' && (
            <Box className="text-center my-3" sx={{ width: '100%', position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Box sx={{ position: 'relative', width: '100%' }}>
                <img src={chapter.image !== null ? chapter.image : placeholderImage} alt={`Illustration for ${chapter.title}`} style={{ maxWidth: '100%', maxHeight: '100%' }} />
                {chapter.image === null && <CircularProgress sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }} />}
                <Tooltip title="Regenerate Image" arrow>
                  <IconButton
                    sx={{ position: 'absolute', top: 2, right: 2, backgroundColor: 'rgba(255, 255, 255, 0.5)' }}
                    onClick={() => handleReloadImage(chapter)}
                    className='btreload d-none'
                    id={`img${chapter.id}`}
                  >
                    <RefreshIcon fontSize="large" />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          )}
        </Box>
      ))}
    </Container>
  );
};

export default Story;