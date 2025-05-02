// src/utils/dateUtils.js

export const formatTimestamp = (timestamp) => {
  if (!timestamp) return "Unknown";
  try {
    const date = new Date(timestamp); 


    const options = {
      year: 'numeric',    
      month: '2-digit',  
      day: '2-digit',    
      hour: '2-digit',    
      minute: '2-digit',  
      second: '2-digit', 
      hour12: true,       
      timeZoneName: 'short' 
    };


    return date.toLocaleString(undefined, options);

  } catch (e) {
    console.error("Error formatting timestamp:", timestamp, e);
    return String(timestamp);
  }
};


