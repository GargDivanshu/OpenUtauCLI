# Use the official .NET SDK image as a base image
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build-env

# Set the working directory in the container
WORKDIR /src

# Copy the solution file and project files
COPY OpenUtau.sln ./
COPY OpenUtau/*.csproj ./OpenUtau/
COPY OpenUtau.Core/*.csproj ./OpenUtau.Core/
COPY OpenUtau.Plugin.Builtin/*.csproj ./OpenUtau.Plugin.Builtin/
COPY OpenUtau.Test/*.csproj ./OpenUtau.Test/

# Restore dependencies
RUN dotnet restore

# Copy the rest of the source code
COPY . ./

# Build the application
RUN dotnet publish OpenUtau/OpenUtau.csproj -c Release -o /app/publish

# Build the runtime image
FROM mcr.microsoft.com/dotnet/runtime:7.0
WORKDIR /app
COPY --from=build-env /app/publish .

# Set the entry point for the container
ENTRYPOINT ["dotnet", "OpenUtau.dll"]