import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Story from './Story';
import { Container, CircularProgress, Box, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import { getUserId } from './utils'; 
import { useLocation } from 'react-router-dom';
import { getStory, illustrateChapter, chapterImageUrl, checkImageExists } from './api';
import { usePrintMode } from './usePrintMode';

const StoryPage = () => {
  const { storyId } = useParams();
  const [story, setStory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [storyTitle, setStoryTitle] = useState('');
  const [chapters, setChapters] = useState([]);
  const [loadingChapters, setLoadingChapters] = useState(true);
  const [editButtonClass, setEditButtonClass] = useState('d-none');

  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const admin = queryParams.get('admin');

  const userCookie = getUserId();

  const fetchChapterImages = async (chapters, storyid) => {
    setLoadingChapters(true);

    const updatedChapters = [...chapters];

    for (let i = 0; i < updatedChapters.length; i++) {
      const chapter = updatedChapters[i];
      const imageUrl = chapterImageUrl(storyid, chapter.id);

      const imageExists = await checkImageExists(imageUrl);

      if (!imageExists) {
        try {
          const data = await illustrateChapter(storyid, chapter.id, chapter.text, userCookie);
          updatedChapters[i].image = data.url;
        } catch (error) {
          console.error(`Error generating image for chapter ${chapter.title}:`, error);
        }
      } else {
        updatedChapters[i].image = imageUrl;
      }

      setChapters([...updatedChapters]);
      
    }
  };

  const updateChapterImage = (chapterId, imageUrl) => {
    setChapters((prevChapters) =>
      prevChapters.map((chapter) =>
        chapter.id === chapterId ? { ...chapter, image: imageUrl } : chapter
      )
    );
  };

  useEffect(() => {
    const fetchStory = async () => {
      setLoading(true);
      try {
        const data = await getStory(storyId, admin || userCookie);
        setStory(data);
        setStoryTitle(data.title);
        setChapters(data.chapters);
        await fetchChapterImages(data.chapters, data.id);
      } catch (err) {
        setError('Error: Failed to load story.');
      }
      setLoading(false);
    };

    fetchStory();
    
  }, [storyId, admin, userCookie]);

  usePrintMode({ toggleReload: true });

  const printStory = () => {
    window.print();
  };


  if (loading) {
    return <Box className="d-flex justify-content-center mt-4"><CircularProgress /></Box>;
  }

  if (error) {
    return <Typography className="mt-4" color="error">{error}</Typography>;
  }

  return (
    <Container className="container p-5">
      {story && <Story title={storyTitle} 
        chapters={chapters} 
        storyId={storyId} 
        userId={userCookie} 
        updateChapterImage={updateChapterImage} 
        loadingChapters={loadingChapters} 
        setLoadingChapters={setLoadingChapters}
        editButtonClass = {editButtonClass}
        setEditButtonClass = {setEditButtonClass}
        />}
      <Box className="d-flex justify-content-center mb-4" id="print-story">
        <Link onClick={printStory}>
          Print Story
        </Link>
      </Box>
      <Box className="d-flex justify-content-center mb-4" id="view-user-library">
        <Link to={`/library`}>
          View User Library
        </Link>
      </Box>
      <Box className="d-flex justify-content-center mb-5" id="create-new-story">
        <Link to={`/`}>
          Create New Story
        </Link>
      </Box>
    </Container>
  );
};

export default StoryPage;
