A Playlist Converter REST API made using FastAPI that converts a spotify playlist to an equivalent YTMusic playlist and vice versa.

Requested playlists are stored in the server's database using mongoDB and allow features like addition, deletion and searching of songs in the playlist.

An advanced search algorithm has been implemented to search songs in the playlists via a prefix by implementing a trie data structure that allows efficient searching of songs having a common prefix.

Future Improvements:

Addition of redis caching,
optimizations for trie data structure,
improved scalability for large playlists