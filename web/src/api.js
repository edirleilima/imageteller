// Single place for talking to the ImageTeller API.
//
// Every backend call lives here so pages don't each re-build URLs, params, and
// axios options. Functions return response.data on success and let axios throw
// on failure, so callers keep their existing try/catch behavior.
//
// The caller's anonymous identity (and the admin token, which is just a special
// identity) travels in the X-User-Id request header rather than the URL query
// string, so it never lands in server/proxy access logs or Referer headers.
import axios from 'axios';

const baseUrl = import.meta.env.VITE_API_BASE_URL;

// Public placeholder image shown while a chapter illustration is generating.
export const placeholderImage = import.meta.env.VITE_PLACEHOLDER_IMAGE_URL;

// Identity header for a given user id (admin token is passed here too).
const userHeaders = (user) => ({ 'X-User-Id': user ?? '' });

const jsonHeaders = (user) => ({
  headers: { 'Content-Type': 'application/json', ...userHeaders(user) },
});

// --- story generation / management ---------------------------------------
export const generateStory = async (formData, genre, user) => {
  const url = new URL(`${baseUrl}/image-to-story/`);
  url.searchParams.append('genre', genre);
  const response = await axios.post(url.toString(), formData, {
    headers: { 'Content-Type': 'multipart/form-data', ...userHeaders(user) },
  });
  return response.data;
};

export const getStories = async (user) => {
  const response = await axios.post(`${baseUrl}/get-stories/`, null, {
    headers: userHeaders(user),
  });
  return response.data;
};

export const getStory = async (id, user) => {
  const response = await axios.post(`${baseUrl}/get-story/`, null, {
    params: { id },
    headers: userHeaders(user),
  });
  return response.data;
};

export const saveStory = async (id, user) => {
  const response = await axios.post(`${baseUrl}/save-story/`, null, {
    params: { id },
    headers: userHeaders(user),
  });
  return response.data;
};

export const deleteStory = async (id, user) => {
  const response = await axios.post(`${baseUrl}/delete-story/`, null, {
    params: { id },
    headers: userHeaders(user),
  });
  return response.data;
};

export const illustrateChapter = async (storyId, chapterId, text, user) => {
  const response = await axios.post(`${baseUrl}/illustrate-chapter/`, {
    story_id: storyId.toString(),
    chapter_id: chapterId.toString(),
    text,
  }, jsonHeaders(user));
  return response.data;
};

export const regenerateChapter = async (storyId, chapterId, user) => {
  const response = await axios.post(`${baseUrl}/regenerate-chapter/`, {
    story_id: storyId.toString(),
    chapter_id: chapterId.toString(),
    text: '',
  }, jsonHeaders(user));
  return response.data;
};

// --- chapter image helpers -----------------------------------------------
export const chapterImageUrl = (storyId, chapterId) =>
  `${baseUrl}/chapters/${storyId}/${chapterId}`;

export const checkImageExists = async (url) => {
  try {
    const response = await fetch(url, { method: 'HEAD' });
    return response.status === 200;
  } catch (error) {
    return false;
  }
};
