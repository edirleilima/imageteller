import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import Story from './Story';
import { Container, CircularProgress, Box, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import { GetCookie } from './utils'; 
import { useLocation } from 'react-router-dom';

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

  const baseUrl = process.env.REACT_APP_API_BASE_URL;

  const userCookie = GetCookie("imageteller_user");

  const fetchChapterImages = async (chapters, storyid) => {
    setLoadingChapters(true);
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
      const chapter = updatedChapters[i];
      const imageUrl = `${baseUrl}/chapters/${storyid}/${chapter.id}`;

      const imageExists = await checkImageExists(imageUrl);

      if (!imageExists) {
        try {
          const response = await axios.post(`${baseUrl}/illustrate-chapter/`, {
            "story_id": storyid.toString(),
            "chapter_id": chapter.id.toString(),
            "text": chapter.text,
            "user": userCookie
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
        const response = await axios.post(`${baseUrl}/get-story/`, null, {
          params: {
            id: storyId,
            user: admin || userCookie
          }
        });
        setStory(response.data);
        setStoryTitle(response.data.title);
        setChapters(response.data.chapters);
        await fetchChapterImages(response.data.chapters, response.data.id);
      } catch (err) {
        setError('Error: Failed to load story.');
      }
      setLoading(false);
    };

    fetchStory();
    
  }, [storyId, admin, userCookie, baseUrl]);

  useEffect(() => {
    const handleBeforePrint = () => {
      document.querySelectorAll('.MuiContainer-root').forEach((element) => {
        element.classList.add('print-container');
        element.classList.remove('MuiContainer-root', 'MuiContainer-maxWidthLg', 'container', 'p-5');
      });
      document.getElementById('view-user-library').classList.add('d-none');
      document.getElementById('create-new-story').classList.add('d-none');
      document.getElementById('print-story').classList.add('d-none');
      document.querySelectorAll('.btreload').forEach(function(element) {
        element.classList.add('d-none');
      });
      document.getElementById('view-user-library').classList.remove('d-flex');
      document.getElementById('create-new-story').classList.remove('d-flex');
      document.getElementById('print-story').classList.remove('d-flex');
    };

    const handleAfterPrint = () => {
      document.querySelectorAll('.print-container').forEach((element) => {
        element.classList.add('MuiContainer-root', 'MuiContainer-maxWidthLg', 'container', 'p-5');
        element.classList.remove('print-container');
      });
      document.getElementById('view-user-library').classList.add('d-flex');
      document.getElementById('create-new-story').classList.add('d-flex');
      document.getElementById('print-story').classList.add('d-flex');
      document.querySelectorAll('.btreload').forEach(function(element) {
        element.classList.add('d-flex');
      });
      document.getElementById('view-user-library').classList.remove('d-none');
      document.getElementById('create-new-story').classList.remove('d-none');
      document.getElementById('print-story').classList.remove('d-none');      
    };

    window.addEventListener('beforeprint', handleBeforePrint);
    window.addEventListener('afterprint', handleAfterPrint);

    return () => {
      window.removeEventListener('beforeprint', handleBeforePrint);
      window.removeEventListener('afterprint', handleAfterPrint);
    };
  }, []);

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
