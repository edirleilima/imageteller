import { v4 as uuidv4 } from 'uuid';

const USER_COOKIE = 'imageteller_user';

export const GetCookie = (cname) => {
  let name = cname + '=';
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return '';
};

export const SetCookie = (cname, cvalue, exdays) => {
  const d = new Date();
  d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
  let expires = 'expires=' + d.toUTCString();
  document.cookie = cname + '=' + cvalue + ';' + expires + ';path=/';
};

// Read the anonymous per-browser user id (empty string if not set yet).
export const getUserId = () => GetCookie(USER_COOKIE);

// Read the user id, creating and persisting one (360 days) if absent.
export const getOrCreateUserId = () => {
  let userid = GetCookie(USER_COOKIE);
  if (userid === '') {
    userid = uuidv4();
    SetCookie(USER_COOKIE, userid, 360);
  }
  return userid;
};
