import { useEffect } from 'react';

// Shared print-mode toggling, previously copy-pasted into Start and ViewStory.
// Reproduces the original handlers exactly. ViewStory additionally hides/shows
// the per-chapter ".btreload" buttons, enabled via { toggleReload: true }.
export function usePrintMode({ toggleReload = false } = {}) {
  useEffect(() => {
    const ids = ['view-user-library', 'create-new-story', 'print-story'];

    const handleBeforePrint = () => {
      document.querySelectorAll('.MuiContainer-root').forEach((element) => {
        element.classList.add('print-container');
        element.classList.remove('MuiContainer-root', 'MuiContainer-maxWidthLg', 'container', 'p-5');
      });
      ids.forEach((id) => document.getElementById(id).classList.add('d-none'));
      if (toggleReload) {
        document.querySelectorAll('.btreload').forEach((element) => {
          element.classList.add('d-none');
        });
      }
      ids.forEach((id) => document.getElementById(id).classList.remove('d-flex'));
    };

    const handleAfterPrint = () => {
      document.querySelectorAll('.print-container').forEach((element) => {
        element.classList.add('MuiContainer-root', 'MuiContainer-maxWidthLg', 'container', 'p-5');
        element.classList.remove('print-container');
      });
      ids.forEach((id) => document.getElementById(id).classList.add('d-flex'));
      if (toggleReload) {
        document.querySelectorAll('.btreload').forEach((element) => {
          element.classList.add('d-flex');
        });
      }
      ids.forEach((id) => document.getElementById(id).classList.remove('d-none'));
    };

    window.addEventListener('beforeprint', handleBeforePrint);
    window.addEventListener('afterprint', handleAfterPrint);

    return () => {
      window.removeEventListener('beforeprint', handleBeforePrint);
      window.removeEventListener('afterprint', handleAfterPrint);
    };
  }, [toggleReload]);
}
