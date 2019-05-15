function shutdownosx
  # cf. http://apple.stackexchange.com/a/103633
  osascript -e 'tell app "System Events" to shut down'
end
