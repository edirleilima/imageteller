import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Start from './Start';
import ViewStory from './ViewStory';
import Library from './Library';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Start />} />
      <Route path="/library" element={<Library />} />
      <Route path="/story/:storyId" element={<ViewStory />} />
    </Routes>
  );
}

export default App;
